"""
Loop Cracker - Infinite loop between Learning AI and Hashcat GPU

The loop:
1. LEARN PHASE: Generate random passwords, learn patterns
2. ATTACK PHASE: Write all patterns to .hcmask, run hashcat GPU
3. If found -> return password
4. If not found -> go back to LEARN PHASE

This continues indefinitely until the password is cracked.
"""
import asyncio
import time
import threading
from typing import Optional, Dict, Callable, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from .storage import get_storage, PatternStorage
from .learning_ai import get_ai, LearningPasswordAI
from .hashcat import get_hashcat, HashcatGPU, HashType, HashcatStatus


class LoopPhase(Enum):
    """Current phase of the loop"""
    IDLE = "idle"
    LEARNING = "learning"
    ATTACKING = "attacking"
    CRACKED = "cracked"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LoopStats:
    """Statistics for the cracking loop"""
    phase: LoopPhase = LoopPhase.IDLE
    target_hash: str = ""
    hash_type: str = "sha256"
    min_length: int = 6
    max_length: int = 10
    current_length: int = 6
    loop_count: int = 0
    patterns_generated: int = 0
    patterns_learned: int = 0
    patterns_tried: int = 0
    masks_current: int = 0
    existing_patterns_used: int = 0
    smart_mode: bool = True  # Use intelligent pattern categories
    current_category: str = ""  # Current category being tried
    exhaustion_progress: int = 0  # Percentage of pattern space exhausted for current length
    categories_done: List[str] = field(default_factory=list)  # Categories already tried for current length
    batch_count: int = 0  # Number of batches processed
    batch_size: int = 5000  # Current batch size
    started_at: Optional[datetime] = None
    current_phase_started: Optional[datetime] = None
    result: Optional[str] = None
    last_error: Optional[str] = None


class LoopCracker:
    """
    Infinite loop cracker that alternates between learning and attacking.

    The strategy:
    - LEARN: Generate N random passwords, learn their patterns
    - ATTACK: Use all learned patterns as hashcat masks, try to crack
    - REPEAT until cracked or stopped
    """

    def __init__(
        self,
        storage: Optional[PatternStorage] = None,
        ai: Optional[LearningPasswordAI] = None,
        hashcat: Optional[HashcatGPU] = None,
        data_dir: Optional[str] = None
    ):
        self.storage = storage or get_storage(data_dir)
        self.ai = ai or get_ai(data_dir)
        self.hashcat = hashcat or get_hashcat()

        self.stats = LoopStats()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Config
        self.learn_batch_size = 500  # Passwords to generate per learn phase
        self.attack_timeout = 60  # Seconds per attack phase (reduced from 120)
        self.max_masks_per_attack = 100  # Limit masks per attack (reduced from 200)
        self.batch_size = 5000  # Patterns per batch for exhaustive mode
        self.min_length: int = 6
        self.max_length: int = 10
        self.smart_mode: bool = True  # Use intelligent pattern categories (default ON)
        self.max_keyspace: int = 100_000_000  # Split masks > 100M into sub-masks
        self.sequential_mode: bool = True  # Test each mask sequentially until exhausted

        # Enabled categories (all enabled by default)
        self.enabled_categories: set = set()

        # Callbacks
        self.on_phase_change: Optional[Callable[[LoopPhase], None]] = None
        self.on_progress: Optional[Callable[[LoopStats], None]] = None
        self.on_cracked: Optional[Callable[[str], None]] = None

    # Pattern categories by real-world frequency
    # Each main category has a _remix variant (dual/hybrid patterns)
    PATTERN_CATEGORIES = [
        # 1. word_date + remix
        {
            "name": "word_date",
            "description": "mot + date (exemple123456)",
            "frequency": 35,
            "priority": 1,
        },
        {
            "name": "word_date_remix",
            "description": "date+mot, mot+date+mot, date+mot+date",
            "frequency": 3,
            "priority": 2,
        },
        # 2. capitalized_digits + remix
        {
            "name": "capitalized_digits",
            "description": "Mot + chiffres (Password123)",
            "frequency": 25,
            "priority": 3,
        },
        {
            "name": "capitalized_digits_remix",
            "description": "chiffres+Mot, Mot+chiffres+mot, chiffres+Mot+chiffres",
            "frequency": 2,
            "priority": 4,
        },
        # 3. word_year + remix
        {
            "name": "word_year",
            "description": "mot + année (admin2024)",
            "frequency": 15,
            "priority": 5,
        },
        {
            "name": "word_year_remix",
            "description": "année+mot, mot+année+mot, année+mot+année",
            "frequency": 1,
            "priority": 6,
        },
        # 4. digits_word + remix
        {
            "name": "digits_word",
            "description": "chiffres + mot (123password)",
            "frequency": 10,
            "priority": 7,
        },
        {
            "name": "digits_word_remix",
            "description": "chiffres+mot+chiffres, mot+chiffres+mot",
            "frequency": 1,
            "priority": 8,
        },
        # 5. word_special_digits
        {
            "name": "word_special_digits",
            "description": "mot + special + chiffres (pass!123)",
            "frequency": 8,
            "priority": 9,
        },
        # 6. word_only + remix
        {
            "name": "word_only",
            "description": "mot seul (password)",
            "frequency": 5,
            "priority": 10,
        },
        {
            "name": "word_only_remix",
            "description": "UPPER+lower, lower+UPPER, alternance (HeLLo)",
            "frequency": 1,
            "priority": 11,
        },
        # 7. other (rares)
        {
            "name": "other",
            "description": "autres combinaisons (rares)",
            "frequency": 1,
            "priority": 12,
        },
        # 8. exhaustive - ALL remaining patterns (LLDUUL, DULSLD, etc.)
        {
            "name": "exhaustive",
            "description": "TOUS les patterns restants (4^N combinaisons)",
            "frequency": 1,
            "priority": 99,  # Last priority - after all smart categories
        },
    ]

    def _get_category_masks(self, category: str, length: int) -> List[str]:
        """Generate masks for a specific category."""
        masks = []

        if category == "word_date":
            # mot + date: lettres puis 4-8 chiffres (dates: DDMMYY, DDMMYYYY, etc.)
            for digits in range(4, min(9, length)):
                letters = length - digits
                if letters >= 2:
                    masks.append("?l" * letters + "?d" * digits)
                    masks.append("?u" + "?l" * (letters - 1) + "?d" * digits)

        elif category == "capitalized_digits":
            # Mot capitalisé + 1-4 chiffres
            for digits in range(1, min(5, length - 1)):
                letters = length - digits
                if letters >= 2:
                    masks.append("?u" + "?l" * (letters - 1) + "?d" * digits)

        elif category == "word_year":
            # mot + 4 chiffres (année: 2024, 1990, etc.)
            if length >= 5:
                letters = length - 4
                masks.append("?l" * letters + "?d?d?d?d")
                if letters >= 2:
                    masks.append("?u" + "?l" * (letters - 1) + "?d?d?d?d")

        elif category == "digits_word":
            # 2-4 chiffres + mot
            for digits in range(2, min(5, length - 2)):
                letters = length - digits
                if letters >= 2:
                    masks.append("?d" * digits + "?l" * letters)
                    masks.append("?d" * digits + "?u" + "?l" * (letters - 1))

        elif category == "word_special_digits":
            # mot + special + chiffres ou mot + chiffres + special
            if length >= 4:
                for letters in range(2, length - 2):
                    remaining = length - letters - 1
                    if remaining >= 1:
                        # mot!123
                        masks.append("?l" * letters + "?s" + "?d" * remaining)
                        # mot123!
                        masks.append("?l" * letters + "?d" * remaining + "?s")
                        # Mot!123
                        if letters >= 2:
                            masks.append("?u" + "?l" * (letters - 1) + "?s" + "?d" * remaining)
                            masks.append("?u" + "?l" * (letters - 1) + "?d" * remaining + "?s")

        elif category == "word_only":
            # mot lowercase ou Capitalisé
            masks.append("?l" * length)
            if length >= 2:
                masks.append("?u" + "?l" * (length - 1))
            # tout majuscule (rare mais existe)
            masks.append("?u" * length)

        # ========== REMIX CATEGORIES (permutations/répétitions avec profondeur) ==========

        elif category == "word_date_remix":
            # Remix de word_date avec profondeur
            # Profondeur 1: date+mot
            for digits in range(2, min(6, length - 1)):
                letters = length - digits
                if letters >= 2:
                    masks.append("?d" * digits + "?l" * letters)
            # Profondeur 2: mot+date+mot, date+mot+date
            for l1 in range(1, length - 2):
                for d in range(1, length - l1 - 1):
                    l2 = length - l1 - d
                    if l2 >= 1:
                        masks.append("?l" * l1 + "?d" * d + "?l" * l2)
            for d1 in range(1, length - 2):
                for l in range(1, length - d1 - 1):
                    d2 = length - d1 - l
                    if d2 >= 1:
                        masks.append("?d" * d1 + "?l" * l + "?d" * d2)
            # Profondeur 3: mot+date+mot+date, date+mot+date+mot
            if length >= 6:
                for l1 in range(1, length - 4):
                    for d1 in range(1, length - l1 - 3):
                        for l2 in range(1, length - l1 - d1 - 1):
                            d2 = length - l1 - d1 - l2
                            if d2 >= 1:
                                masks.append("?l" * l1 + "?d" * d1 + "?l" * l2 + "?d" * d2)
                for d1 in range(1, length - 4):
                    for l1 in range(1, length - d1 - 3):
                        for d2 in range(1, length - d1 - l1 - 1):
                            l2 = length - d1 - l1 - d2
                            if l2 >= 1:
                                masks.append("?d" * d1 + "?l" * l1 + "?d" * d2 + "?l" * l2)
            # Profondeur 4: mot+date+mot+date+mot (si length >= 8)
            if length >= 8:
                for l1 in range(1, length - 6):
                    for d1 in range(1, length - l1 - 5):
                        for l2 in range(1, length - l1 - d1 - 3):
                            for d2 in range(1, length - l1 - d1 - l2 - 1):
                                l3 = length - l1 - d1 - l2 - d2
                                if l3 >= 1:
                                    masks.append("?l" * l1 + "?d" * d1 + "?l" * l2 + "?d" * d2 + "?l" * l3)

        elif category == "capitalized_digits_remix":
            # Remix de capitalized_digits avec profondeur
            # Profondeur 1: chiffres+Mot
            for digits in range(1, min(5, length - 1)):
                letters = length - digits
                if letters >= 2:
                    masks.append("?d" * digits + "?u" + "?l" * (letters - 1))
            # Profondeur 2: Mot+chiffres+mot, chiffres+Mot+chiffres
            for l1 in range(2, length - 1):
                for d in range(1, min(4, length - l1)):
                    l2 = length - l1 - d
                    if l2 >= 1:
                        masks.append("?u" + "?l" * (l1 - 1) + "?d" * d + "?l" * l2)
            for d1 in range(1, min(4, length - 2)):
                for l in range(2, length - d1):
                    d2 = length - d1 - l
                    if d2 >= 1:
                        masks.append("?d" * d1 + "?u" + "?l" * (l - 1) + "?d" * d2)
            # Profondeur 3: Mot+chiffres+mot+chiffres
            if length >= 6:
                for l1 in range(2, length - 3):
                    for d1 in range(1, length - l1 - 2):
                        for l2 in range(1, length - l1 - d1 - 1):
                            d2 = length - l1 - d1 - l2
                            if d2 >= 1:
                                masks.append("?u" + "?l" * (l1 - 1) + "?d" * d1 + "?l" * l2 + "?d" * d2)

        elif category == "word_year_remix":
            # Remix de word_year avec profondeur (année = 4 chiffres)
            # Profondeur 1: année+mot
            if length >= 5:
                letters = length - 4
                masks.append("?d?d?d?d" + "?l" * letters)
                if letters >= 2:
                    masks.append("?d?d?d?d" + "?u" + "?l" * (letters - 1))
            # Profondeur 2: mot+année+mot
            if length >= 6:
                for l1 in range(1, length - 4):
                    l2 = length - l1 - 4
                    if l2 >= 1:
                        masks.append("?l" * l1 + "?d?d?d?d" + "?l" * l2)
                        if l1 >= 1:
                            masks.append("?u" + "?l" * (l1 - 1) + "?d?d?d?d" + "?l" * l2)
            # Profondeur 3: année+mot+année
            if length >= 9:
                letters = length - 8
                if letters >= 1:
                    masks.append("?d?d?d?d" + "?l" * letters + "?d?d?d?d")
            # Profondeur 4: mot+année+mot+année
            if length >= 10:
                for l1 in range(1, length - 9):
                    l2 = length - l1 - 8
                    if l2 >= 1:
                        masks.append("?l" * l1 + "?d?d?d?d" + "?l" * l2 + "?d?d?d?d")

        elif category == "digits_word_remix":
            # Remix de digits_word avec profondeur
            # Profondeur 2: chiffres+mot+chiffres, mot+chiffres+mot
            for d1 in range(1, length - 2):
                for l in range(1, length - d1 - 1):
                    d2 = length - d1 - l
                    if d2 >= 1:
                        masks.append("?d" * d1 + "?l" * l + "?d" * d2)
            for l1 in range(1, length - 2):
                for d in range(1, length - l1 - 1):
                    l2 = length - l1 - d
                    if l2 >= 1:
                        masks.append("?l" * l1 + "?d" * d + "?l" * l2)
            # Profondeur 3: chiffres+mot+chiffres+mot, mot+chiffres+mot+chiffres
            if length >= 6:
                for d1 in range(1, length - 4):
                    for l1 in range(1, length - d1 - 3):
                        for d2 in range(1, length - d1 - l1 - 1):
                            l2 = length - d1 - l1 - d2
                            if l2 >= 1:
                                masks.append("?d" * d1 + "?l" * l1 + "?d" * d2 + "?l" * l2)
                for l1 in range(1, length - 4):
                    for d1 in range(1, length - l1 - 3):
                        for l2 in range(1, length - l1 - d1 - 1):
                            d2 = length - l1 - d1 - l2
                            if d2 >= 1:
                                masks.append("?l" * l1 + "?d" * d1 + "?l" * l2 + "?d" * d2)

        elif category == "word_only_remix":
            # Remix de word_only avec profondeur (upper/lower)
            # Profondeur 1: UPPER+lower, lower+UPPER
            if length >= 2:
                for u in range(1, length):
                    l = length - u
                    if l >= 1:
                        masks.append("?u" * u + "?l" * l)
                        masks.append("?l" * l + "?u" * u)
            # Profondeur 2: upper+lower+upper, lower+upper+lower
            if length >= 3:
                for u1 in range(1, length - 1):
                    for l in range(1, length - u1):
                        u2 = length - u1 - l
                        if u2 >= 1:
                            masks.append("?u" * u1 + "?l" * l + "?u" * u2)
                for l1 in range(1, length - 1):
                    for u in range(1, length - l1):
                        l2 = length - l1 - u
                        if l2 >= 1:
                            masks.append("?l" * l1 + "?u" * u + "?l" * l2)
            # Alternance U/L
            if length >= 2:
                alt1 = "".join("?u" if i % 2 == 0 else "?l" for i in range(length))
                alt2 = "".join("?l" if i % 2 == 0 else "?u" for i in range(length))
                masks.append(alt1)
                masks.append(alt2)

        elif category == "other":
            # Autres combinaisons rares
            if length >= 4:
                # special au début/milieu/fin
                masks.append("?s" + "?l" * (length - 1))
                masks.append("?l" * (length - 1) + "?s")
                masks.append("?s" + "?d" * (length - 1))
                masks.append("?d" * (length - 1) + "?s")
                if length >= 5:
                    mid = length // 2
                    masks.append("?l" * mid + "?s" + "?l" * (length - mid - 1))
                    masks.append("?l" * mid + "?s" + "?d" * (length - mid - 1))
                    masks.append("?d" * mid + "?s" + "?d" * (length - mid - 1))

                # tout chiffres (PIN codes, etc.)
                masks.append("?d" * length)

                # special + mot + special
                if length >= 3:
                    masks.append("?s" + "?l" * (length - 2) + "?s")
                    masks.append("?s" + "?d" * (length - 2) + "?s")

                # upper + lower mélangés
                if length >= 4:
                    # UlUl ou lUlU
                    alt_ul = ""
                    alt_lu = ""
                    for i in range(length):
                        alt_ul += "?u" if i % 2 == 0 else "?l"
                        alt_lu += "?l" if i % 2 == 0 else "?u"
                    masks.append(alt_ul)
                    masks.append(alt_lu)

        elif category == "exhaustive":
            # TOUS les patterns possibles (4^N) SAUF ceux déjà couverts
            # Collecte les masks des autres catégories pour les exclure
            already_covered = set()
            for other_cat in self.PATTERN_CATEGORIES:
                if other_cat["name"] != "exhaustive":
                    for m in self._get_category_masks(other_cat["name"], length):
                        already_covered.add(m)

            # Génère TOUS les patterns L/U/D/S
            chars = ['L', 'U', 'D', 'S']
            char_to_mask = {'L': '?l', 'U': '?u', 'D': '?d', 'S': '?s'}
            total = 4 ** length

            for idx in range(total):
                # Convert index to pattern (base-4)
                pattern = []
                temp = idx
                for _ in range(length):
                    pattern.append(chars[temp % 4])
                    temp //= 4
                pattern = list(reversed(pattern))

                # Convert to mask
                mask = "".join(char_to_mask[c] for c in pattern)

                # Skip if already covered by other categories
                if mask not in already_covered:
                    masks.append(mask)

        return masks

    def _get_category_masks_range(self, category: str, min_length: int, max_length: int) -> List[str]:
        """Generate masks for a specific category across ALL lengths in the range."""
        all_masks = []
        seen = set()
        for length in range(min_length, max_length + 1):
            for mask in self._get_category_masks(category, length):
                if mask not in seen:
                    all_masks.append(mask)
                    seen.add(mask)
        return all_masks

    def _get_priority_masks(self, length: int) -> List[str]:
        """
        Get high-priority masks organized by category.
        Returns masks sorted by real-world frequency.

        If smart_mode is OFF, returns empty list (use brute force patterns).
        """
        if not self.smart_mode:
            return []  # No priority masks in brute force mode

        all_masks = []
        seen = set()

        # Process categories in priority order
        for category in sorted(self.PATTERN_CATEGORIES, key=lambda x: x["priority"]):
            self.stats.current_category = category["name"]
            category_masks = self._get_category_masks(category["name"], length)
            for mask in category_masks:
                if mask not in seen:
                    all_masks.append(mask)
                    seen.add(mask)

        return all_masks

    def _get_priority_masks_range(self, min_length: int, max_length: int) -> List[str]:
        """
        Get high-priority masks for ALL lengths in the range.
        This ensures remix patterns cover all possible lengths.
        """
        if not self.smart_mode:
            return []

        all_masks = []
        seen = set()

        # Process categories in priority order
        for category in sorted(self.PATTERN_CATEGORIES, key=lambda x: x["priority"]):
            self.stats.current_category = category["name"]
            # Get masks for ALL lengths in range
            category_masks = self._get_category_masks_range(
                category["name"], min_length, max_length
            )
            for mask in category_masks:
                if mask not in seen:
                    all_masks.append(mask)
                    seen.add(mask)

        return all_masks

    def get_category_info(self) -> List[Dict]:
        """Get information about pattern categories for UI with enabled status."""
        result = []
        for cat in self.PATTERN_CATEGORIES:
            cat_info = cat.copy()
            # If no categories set, all are enabled
            cat_info["enabled"] = len(self.enabled_categories) == 0 or cat["name"] in self.enabled_categories
            result.append(cat_info)
        return result

    def set_enabled_categories(self, categories: List[str]):
        """Set which categories are enabled. Empty list = all enabled."""
        valid_names = {c["name"] for c in self.PATTERN_CATEGORIES}
        self.enabled_categories = set(c for c in categories if c in valid_names)
        print(f"[LOOP] Enabled categories: {self.enabled_categories if self.enabled_categories else 'ALL'}")

    def get_enabled_categories(self) -> List[str]:
        """Get list of enabled categories. Empty = all enabled."""
        if not self.enabled_categories:
            return [c["name"] for c in self.PATTERN_CATEGORIES]
        return list(self.enabled_categories)

    def is_category_enabled(self, category_name: str) -> bool:
        """Check if a category is enabled."""
        # Empty set = all enabled
        return len(self.enabled_categories) == 0 or category_name in self.enabled_categories

    def set_smart_mode(self, enabled: bool):
        """Enable or disable smart mode (intelligent pattern categories)."""
        self.smart_mode = enabled
        self.stats.smart_mode = enabled

    def is_smart_mode(self) -> bool:
        """Check if smart mode is enabled."""
        return self.smart_mode

    def _set_phase(self, phase: LoopPhase):
        """Update phase and notify"""
        self.stats.phase = phase
        self.stats.current_phase_started = datetime.now()
        if self.on_phase_change:
            self.on_phase_change(phase)
        if self.on_progress:
            self.on_progress(self.stats)

    def _learn_phase(self, length: int) -> int:
        """
        LEARN PHASE: Generate patterns for this length.

        Always uses batch generation with progress tracking (never loads all in memory)

        Returns: Number of NEW patterns generated (0 if exhausted)
        """
        self._set_phase(LoopPhase.LEARNING)

        # Count patterns before
        patterns_before = len(self.ai.patterns)

        # Generate patterns (exhaustive for short, batched for long)
        patterns = self.ai.generate_exhaustive_patterns(length, skip_weak=True)
        self.stats.patterns_learned = len(self.ai.patterns)

        # Track NEW patterns generated
        new_patterns = len(self.ai.patterns) - patterns_before
        self.stats.patterns_generated += new_patterns

        # Update exhaustion progress in stats
        progress = self.ai.get_exhaustion_progress(length)
        self.stats.exhaustion_progress = progress.get("progress_pct", 0)

        return new_patterns

    def _clear_length_memory(self, length: int):
        """Clear patterns for a length from memory after attack."""
        self.ai.clear_patterns_for_length(length)

    def _attack_phase(self, target_hash: str, hash_type: HashType, length: int) -> Optional[str]:
        """
        ATTACK PHASE: Use all learned patterns as hashcat masks.
        Priority order:
        1. High-priority masks (word+date, capitalized+digits, etc.)
        2. Learned patterns from storage
        3. AI-generated patterns
        """
        self._set_phase(LoopPhase.ATTACKING)

        # START with priority masks (word+date patterns)
        priority_masks = self._get_priority_masks(length)

        # Get learned masks from storage
        storage_masks = self.storage.get_masks_for_length(length, limit=self.max_masks_per_attack)

        # Add masks from AI patterns
        ai_masks = self.ai.get_top_masks(length, limit=50)

        # Build final mask list: priority first, then storage, then AI
        masks = []
        seen = set()

        # 1. Priority masks FIRST
        for m in priority_masks:
            if m not in seen:
                masks.append(m)
                seen.add(m)

        # 2. Storage masks
        for m in storage_masks:
            if m not in seen:
                masks.append(m)
                seen.add(m)

        # 3. AI masks
        for m in ai_masks:
            if m not in seen:
                masks.append(m)
                seen.add(m)

        self.stats.masks_current = len(masks)
        self.stats.patterns_tried += len(masks)

        if not masks:
            return None

        # Run hashcat with all masks
        result = self.hashcat.crack_hcmask(
            target_hash,
            masks,
            hash_type,
            timeout=self.attack_timeout
        )

        return result

    def _run_loop(self, target_hash: str, hash_type: HashType, min_length: int, max_length: int):
        """
        Main loop thread - Memory-efficient category-by-category attack.

        Strategy:
        1. For each length in range:
           a. For each category (word_date, capitalized_digits, etc.):
              - Generate masks for this category
              - Attack with hashcat
              - Clear masks from memory
              - Mark category as done for this length
           b. After all categories done, try exhaustive patterns in batches
        """
        self.stats = LoopStats(
            phase=LoopPhase.ATTACKING,
            target_hash=target_hash,
            hash_type=hash_type.name,
            min_length=min_length,
            max_length=max_length,
            current_length=min_length,
            started_at=datetime.now()
        )

        # Track which categories are done for each length
        # Key: length, Value: set of category names done
        categories_done_by_length: Dict[int, set] = {
            l: set() for l in range(min_length, max_length + 1)
        }

        # Load previous progress from storage
        for length in range(min_length, max_length + 1):
            done_key = f"_categories_done_{length}"
            done_list = self.storage.load_state(done_key, [])
            categories_done_by_length[length] = set(done_list)

        while not self._stop_event.is_set():
            self.stats.loop_count += 1
            any_work_done = False

            try:
                # Iterate over each length in range
                for length in range(min_length, max_length + 1):
                    if self._stop_event.is_set():
                        break

                    self.stats.current_length = length
                    self.stats.categories_done = list(categories_done_by_length[length])

                    # PHASE 1: Attack each category with EXHAUSTIVE SUBMASK technique
                    for category in sorted(self.PATTERN_CATEGORIES, key=lambda x: x["priority"]):
                        if self._stop_event.is_set():
                            break

                        cat_name = category["name"]

                        # Skip if category is disabled
                        if not self.is_category_enabled(cat_name):
                            continue

                        # Generate base masks for this category
                        base_masks = self._get_category_masks(cat_name, length)

                        if not base_masks:
                            continue

                        # Check if category is already exhausted for this length
                        cat_progress = self.ai.get_category_progress(
                            cat_name, length, base_masks, self.max_keyspace
                        )

                        if cat_progress["exhausted"]:
                            # Already done - skip
                            if cat_name not in categories_done_by_length[length]:
                                categories_done_by_length[length].add(cat_name)
                            continue

                        any_work_done = True
                        self.stats.current_category = cat_name
                        self.stats.exhaustion_progress = cat_progress["progress_pct"]
                        self._set_phase(LoopPhase.LEARNING)

                        # Use exhaustive submask iterator for ALL categories
                        for masks_batch, progress_pct in self.ai.get_category_submasks_iterator(
                            cat_name,
                            length,
                            base_masks,
                            batch_size=self.batch_size,
                            max_keyspace=self.max_keyspace
                        ):
                            if self._stop_event.is_set():
                                break

                            self._set_phase(LoopPhase.ATTACKING)
                            self.stats.current_category = f"{cat_name}"
                            self.stats.batch_count += 1
                            self.stats.masks_current = len(masks_batch)
                            self.stats.patterns_tried += len(masks_batch)
                            self.stats.exhaustion_progress = progress_pct

                            # Attack with this batch - NO additional splitting needed
                            # (submasks are already sized correctly)
                            if self.sequential_mode:
                                result = self.hashcat.crack_masks_sequential(
                                    target_hash,
                                    masks_batch,
                                    hash_type,
                                    timeout_per_mask=0,
                                    max_keyspace=0  # Already split, don't re-split
                                )
                            else:
                                result = self.hashcat.crack_hcmask(
                                    target_hash,
                                    masks_batch,
                                    hash_type,
                                    timeout=self.attack_timeout
                                )

                            if result:
                                return self._handle_cracked(target_hash, hash_type, result)

                            if self.on_progress:
                                self.on_progress(self.stats)

                        # Mark category as done for this length
                        categories_done_by_length[length].add(cat_name)
                        self.stats.categories_done = list(categories_done_by_length[length])

                        # Save progress
                        done_key = f"_categories_done_{length}"
                        self.storage.save_state(done_key, list(categories_done_by_length[length]))

                        if self.on_progress:
                            self.on_progress(self.stats)

                    # PHASE 2: After all categories, try exhaustive patterns in batches
                    # Batch mode - use iterator to avoid loading all in memory
                    if not self._stop_event.is_set():
                        # Check if exhaustive is already done for this length
                        progress = self.ai.get_exhaustion_progress(length)

                        if not progress["exhausted"]:
                            any_work_done = True
                            self.stats.current_category = "exhaustive_batch"
                            self.stats.exhaustion_progress = progress["progress_pct"]

                            # Use batch iterator - only ONE batch in memory at a time
                            for masks_batch in self.ai.get_masks_batch_iterator(
                                length,
                                batch_size=self.batch_size,
                                skip_weak=True
                            ):
                                if self._stop_event.is_set():
                                    break

                                self._set_phase(LoopPhase.ATTACKING)
                                self.stats.batch_count += 1
                                self.stats.masks_current = len(masks_batch)
                                self.stats.patterns_tried += len(masks_batch)

                                # Update exhaustion progress
                                progress = self.ai.get_exhaustion_progress(length)
                                self.stats.exhaustion_progress = progress["progress_pct"]

                                # Attack with this batch - sequential mode for proper exhaustion
                                if self.sequential_mode:
                                    result = self.hashcat.crack_masks_sequential(
                                        target_hash,
                                        masks_batch,
                                        hash_type,
                                        timeout_per_mask=self.attack_timeout,
                                        max_keyspace=self.max_keyspace
                                    )
                                else:
                                    result = self.hashcat.crack_hcmask(
                                        target_hash,
                                        masks_batch,
                                        hash_type,
                                        timeout=self.attack_timeout
                                    )

                                if result:
                                    return self._handle_cracked(target_hash, hash_type, result)

                                # masks_batch is automatically freed after loop iteration

                                if self.on_progress:
                                    self.on_progress(self.stats)

                            if self.on_progress:
                                self.on_progress(self.stats)

                # If no work was done in this loop, all patterns exhausted
                if not any_work_done:
                    self.stats.current_category = "ALL EXHAUSTED"
                    self._set_phase(LoopPhase.STOPPED)
                    print("[LOOP] All patterns exhausted for all lengths!")
                    break

                if self.on_progress:
                    self.on_progress(self.stats)

            except Exception as e:
                self.stats.last_error = str(e)
                self._set_phase(LoopPhase.ERROR)
                print(f"[LOOP] Error: {e}")
                time.sleep(1)

        self._set_phase(LoopPhase.STOPPED)
        self._running = False

    def _handle_cracked(self, target_hash: str, hash_type: HashType, result: str):
        """Handle successful crack"""
        self.stats.result = result
        self._set_phase(LoopPhase.CRACKED)

        # Save to storage
        pattern = self.ai.get_pattern(result)
        self.storage.add_cracked(
            target_hash, result, hash_type.name.lower(),
            pattern=pattern, method="loop_cracker"
        )

        # Learn from cracked password
        self.ai.learn(result)

        if self.on_cracked:
            self.on_cracked(result)

        self._running = False

    def reset_progress(self, min_length: int = 4, max_length: int = 16):
        """
        Reset all progress tracking for a fresh start.
        Clears categories done and pattern exhaustion progress.
        """
        print(f"[LOOP] Resetting progress for lengths {min_length}-{max_length}")
        for length in range(min_length, max_length + 1):
            # Reset categories done
            done_key = f"_categories_done_{length}"
            self.storage.save_state(done_key, [])
            # Reset pattern exhaustion progress
            progress_key = f"_progress_{length}"
            self.storage.save_state(progress_key, 0)
        print("[LOOP] Progress reset complete")

    def start(
        self,
        target_hash: str,
        hash_type: str = "sha256",
        min_length: int = 6,
        max_length: int = 10,
        smart_mode: bool = True,
        fresh_start: bool = True
    ):
        """
        Start the infinite loop cracker.

        Args:
            target_hash: The hash to crack
            hash_type: Hash type (md5, sha1, sha256, sha512)
            min_length: Minimum password length to target
            max_length: Maximum password length to target
            smart_mode: Use intelligent pattern categories (default True)
            fresh_start: Reset progress and start from scratch (default True)
        """
        # Set smart mode
        self.set_smart_mode(smart_mode)

        # Reset progress if fresh start
        if fresh_start:
            self.reset_progress(min_length, max_length)
        if self._running:
            raise RuntimeError("Loop already running")

        # Check if already cracked
        existing = self.storage.get_cracked(target_hash)
        if existing:
            self.stats.result = existing
            self.stats.phase = LoopPhase.CRACKED
            return existing

        # Parse hash type
        hash_types = {
            "md5": HashType.MD5,
            "sha1": HashType.SHA1,
            "sha256": HashType.SHA256,
            "sha512": HashType.SHA512,
        }
        ht = hash_types.get(hash_type.lower(), HashType.SHA256)

        self.min_length = min_length
        self.max_length = max_length

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(target_hash, ht, min_length, max_length),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Stop the loop"""
        self._stop_event.set()
        self.hashcat.stop()
        if self._thread:
            self._thread.join(timeout=5)
        self._running = False
        self._set_phase(LoopPhase.STOPPED)

    def is_running(self) -> bool:
        """Check if loop is running"""
        return self._running

    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            "phase": self.stats.phase.value,
            "target_hash": self.stats.target_hash[:16] + "..." if self.stats.target_hash else "",
            "hash_type": self.stats.hash_type,
            "min_length": self.stats.min_length,
            "max_length": self.stats.max_length,
            "current_length": self.stats.current_length,
            "loop_count": self.stats.loop_count,
            "patterns_generated": self.stats.patterns_generated,
            "patterns_learned": self.stats.patterns_learned,
            "patterns_tried": self.stats.patterns_tried,
            "masks_current": self.stats.masks_current,
            "existing_patterns_used": self.stats.existing_patterns_used,
            "smart_mode": self.smart_mode,
            "current_category": self.stats.current_category,
            "exhaustion_progress": self.stats.exhaustion_progress,
            "batch_count": self.stats.batch_count,
            "batch_size": self.batch_size,
            "max_keyspace": self.max_keyspace,
            "sequential_mode": self.sequential_mode,
            "running": self._running,
            "result": self.stats.result,
            "started_at": self.stats.started_at.isoformat() if self.stats.started_at else None,
            "duration_seconds": (datetime.now() - self.stats.started_at).total_seconds()
                if self.stats.started_at else 0,
            "last_error": self.stats.last_error
        }

    def get_learned_patterns(self, limit: int = 50) -> List[Dict]:
        """Get patterns learned so far"""
        return self.storage.get_patterns(limit=limit)


# Singleton
_cracker: Optional[LoopCracker] = None

def get_cracker(data_dir: Optional[str] = None) -> LoopCracker:
    """Get or create loop cracker instance"""
    global _cracker
    if _cracker is None:
        _cracker = LoopCracker(data_dir=data_dir)
    return _cracker
