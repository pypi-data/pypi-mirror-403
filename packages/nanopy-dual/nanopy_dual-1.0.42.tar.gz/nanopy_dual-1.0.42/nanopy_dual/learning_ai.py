"""
Learning AI - Pattern-based password generation with self-improvement
"""
import random
import string
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from .storage import get_storage


class LearningPasswordAI:
    """
    Self-improving password generator that learns patterns.

    Phases:
    1. Bootstrap - Random generation to learn initial patterns
    2. Pattern-based - Use common patterns with high weights
    3. Weighted - Position-weighted character selection
    4. Markov - Bigram/trigram chain generation
    5. Genetic - Evolve population using crossover and mutation
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.storage = get_storage(data_dir)

        # Character sets
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Learning state
        self.bigrams: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.trigrams: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.position_weights: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.patterns: Dict[str, int] = defaultdict(int)
        self.total_learned = 0
        self.generation = 0

        # Genetic algorithm
        self.population: List[str] = []
        self.population_size = 100
        self.mutation_rate = 0.1

        # Load saved state
        self._load_state()

    def _load_state(self):
        """Load learning state from storage"""
        self.bigrams = defaultdict(lambda: defaultdict(int),
            {k: defaultdict(int, v) for k, v in
             self.storage.load_state("bigrams", {}).items()})

        self.trigrams = defaultdict(lambda: defaultdict(int),
            {k: defaultdict(int, v) for k, v in
             self.storage.load_state("trigrams", {}).items()})

        self.position_weights = defaultdict(lambda: defaultdict(int),
            {int(k): defaultdict(int, v) for k, v in
             self.storage.load_state("position_weights", {}).items()})

        # Load patterns from learning_state first
        self.patterns = defaultdict(int, self.storage.load_state("patterns", {}))

        # ALSO load patterns from SQLite patterns table (for exhaustive patterns)
        db_patterns = self.storage.get_patterns(limit=100000, min_count=1)
        for p in db_patterns:
            pattern = p["pattern"]
            count = p["count"]
            if pattern not in self.patterns or self.patterns[pattern] < count:
                self.patterns[pattern] = count

        self.total_learned = self.storage.load_state("total_learned", 0)
        self.generation = self.storage.load_state("generation", 0)

        print(f"[AI] Loaded {len(self.patterns)} patterns from DB")

    def _save_state(self):
        """Save learning state to storage"""
        self.storage.save_state("bigrams", dict(self.bigrams))
        self.storage.save_state("trigrams", dict(self.trigrams))
        self.storage.save_state("position_weights",
            {str(k): dict(v) for k, v in self.position_weights.items()})
        self.storage.save_state("patterns", dict(self.patterns))
        self.storage.save_state("total_learned", self.total_learned)
        self.storage.save_state("generation", self.generation)

    # ========== PATTERN EXTRACTION ==========

    def get_pattern(self, password: str) -> str:
        """
        Extract pattern from password.
        L=lowercase, U=uppercase, D=digit, S=special
        """
        pattern = ""
        for c in password:
            if c in self.lowercase:
                pattern += "L"
            elif c in self.uppercase:
                pattern += "U"
            elif c in self.digits:
                pattern += "D"
            else:
                pattern += "S"
        return pattern

    def pattern_to_mask(self, pattern: str) -> str:
        """Convert pattern to hashcat mask"""
        mask_map = {"L": "?l", "U": "?u", "D": "?d", "S": "?s"}
        return "".join(mask_map.get(c, "?a") for c in pattern)

    # ========== LEARNING ==========

    def learn(self, password: str):
        """Learn from a password"""
        if not password:
            return

        # Learn pattern
        pattern = self.get_pattern(password)
        self.patterns[pattern] += 1

        # Store in database
        mask = self.pattern_to_mask(pattern)
        self.storage.add_pattern(pattern, mask)

        # Learn bigrams
        for i in range(len(password) - 1):
            self.bigrams[password[i]][password[i + 1]] += 1

        # Learn trigrams
        for i in range(len(password) - 2):
            self.trigrams[password[i:i+2]][password[i + 2]] += 1

        # Learn position weights
        for i, c in enumerate(password):
            self.position_weights[i][c] += 1

        self.total_learned += 1

        # Save periodically
        if self.total_learned % 100 == 0:
            self._save_state()

    def learn_batch(self, passwords: List[str]):
        """Learn from multiple passwords"""
        for pwd in passwords:
            self.learn(pwd)
        self._save_state()

    # ========== GENERATION METHODS ==========

    def generate_random(self, length: int = 8, include_special: bool = True) -> str:
        """Generate completely random password"""
        chars = self.lowercase + self.uppercase + self.digits
        if include_special and random.random() < 0.3:  # 30% chance to include specials
            chars += self.special
        return "".join(random.choice(chars) for _ in range(length))

    def generate_from_pattern(self, pattern: str) -> str:
        """Generate password from pattern"""
        result = ""
        for c in pattern:
            if c == "L":
                result += random.choice(self.lowercase)
            elif c == "U":
                result += random.choice(self.uppercase)
            elif c == "D":
                result += random.choice(self.digits)
            elif c == "S":
                result += random.choice(self.special)
            else:
                result += random.choice(self.lowercase + self.uppercase + self.digits)
        return result

    def generate_weighted(self, length: int = 8) -> str:
        """Generate using position-weighted character selection"""
        result = ""
        for i in range(length):
            if self.position_weights[i]:
                chars = list(self.position_weights[i].keys())
                weights = list(self.position_weights[i].values())
                result += random.choices(chars, weights=weights)[0]
            else:
                result += random.choice(self.lowercase + self.uppercase + self.digits)
        return result

    def generate_markov(self, length: int = 8) -> str:
        """Generate using Markov chains (bigrams/trigrams)"""
        if not self.bigrams:
            return self.generate_random(length)

        # Start with weighted first char
        if self.position_weights[0]:
            chars = list(self.position_weights[0].keys())
            weights = list(self.position_weights[0].values())
            result = random.choices(chars, weights=weights)[0]
        else:
            result = random.choice(list(self.bigrams.keys()) or list(self.lowercase))

        while len(result) < length:
            # Try trigram first
            if len(result) >= 2 and result[-2:] in self.trigrams:
                next_chars = self.trigrams[result[-2:]]
                if next_chars:
                    chars = list(next_chars.keys())
                    weights = list(next_chars.values())
                    result += random.choices(chars, weights=weights)[0]
                    continue

            # Fall back to bigram
            if result[-1] in self.bigrams:
                next_chars = self.bigrams[result[-1]]
                if next_chars:
                    chars = list(next_chars.keys())
                    weights = list(next_chars.values())
                    result += random.choices(chars, weights=weights)[0]
                    continue

            # Random fallback
            result += random.choice(self.lowercase + self.uppercase + self.digits)

        return result[:length]

    def generate_genetic(self, length: int = 8) -> str:
        """Generate using genetic algorithm"""
        # Initialize population if empty
        if not self.population:
            self.population = [self.generate_random(length) for _ in range(self.population_size)]

        # Selection (tournament)
        def fitness(pwd: str) -> float:
            score = 0
            pattern = self.get_pattern(pwd)
            score += self.patterns.get(pattern, 0) * 10

            for i in range(len(pwd) - 1):
                score += self.bigrams[pwd[i]].get(pwd[i + 1], 0)

            return score

        # Select parents
        tournament_size = 5
        parents = []
        for _ in range(2):
            tournament = random.sample(self.population, min(tournament_size, len(self.population)))
            winner = max(tournament, key=fitness)
            parents.append(winner)

        # Crossover
        crossover_point = random.randint(1, length - 1)
        child = parents[0][:crossover_point] + parents[1][crossover_point:]

        # Mutation
        if random.random() < self.mutation_rate:
            pos = random.randint(0, len(child) - 1)
            chars = self.lowercase + self.uppercase + self.digits
            child = child[:pos] + random.choice(chars) + child[pos + 1:]

        # Add to population, remove worst
        self.population.append(child)
        if len(self.population) > self.population_size:
            self.population.sort(key=fitness, reverse=True)
            self.population = self.population[:self.population_size]

        self.generation += 1
        return child

    def generate(self, length: int = 8, method: str = "auto") -> str:
        """
        Generate password using specified or auto-selected method.

        Methods: random, pattern, weighted, markov, genetic, auto
        """
        if method == "random":
            return self.generate_random(length)

        if method == "pattern":
            # Use most common pattern of this length
            length_patterns = {p: c for p, c in self.patterns.items() if len(p) == length}
            if length_patterns:
                pattern = max(length_patterns, key=length_patterns.get)
                return self.generate_from_pattern(pattern)
            return self.generate_random(length)

        if method == "weighted":
            return self.generate_weighted(length)

        if method == "markov":
            return self.generate_markov(length)

        if method == "genetic":
            return self.generate_genetic(length)

        # Auto mode - choose based on learning progress
        if self.total_learned < 100:
            # Bootstrap phase
            return self.generate_random(length)
        elif self.total_learned < 500:
            # Mix random and pattern
            if random.random() < 0.5:
                return self.generate_random(length)
            return self.generate(length, "pattern")
        elif self.total_learned < 1000:
            # Use weighted and markov
            if random.random() < 0.5:
                return self.generate_weighted(length)
            return self.generate_markov(length)
        else:
            # Full evolution - mix all methods
            r = random.random()
            if r < 0.2:
                return self.generate_random(length)
            elif r < 0.4:
                return self.generate(length, "pattern")
            elif r < 0.6:
                return self.generate_weighted(length)
            elif r < 0.8:
                return self.generate_markov(length)
            else:
                return self.generate_genetic(length)

    def generate_batch(self, count: int, length: int = 8, method: str = "auto") -> List[str]:
        """Generate multiple passwords"""
        return [self.generate(length, method) for _ in range(count)]

    # ========== PATTERN CROSSOVER ==========

    def crossover_patterns(self, length: int, count: int = 50) -> List[str]:
        """
        Generate new patterns by crossing over existing patterns.
        This creates hybrid patterns that may not exist yet.
        """
        # Get existing patterns for this length
        length_patterns = [p for p in self.patterns.keys() if len(p) == length]

        if len(length_patterns) < 2:
            return []

        new_patterns = set()
        chars = ['L', 'U', 'D', 'S']

        for _ in range(count):
            # Method 1: Crossover two patterns
            if random.random() < 0.5 and len(length_patterns) >= 2:
                p1, p2 = random.sample(length_patterns, 2)
                crossover_point = random.randint(1, length - 1)
                new_pattern = p1[:crossover_point] + p2[crossover_point:]
                new_patterns.add(new_pattern)

            # Method 2: Mutation of existing pattern
            elif length_patterns:
                p = random.choice(length_patterns)
                p_list = list(p)
                # Mutate 1-2 positions
                for _ in range(random.randint(1, 2)):
                    pos = random.randint(0, length - 1)
                    p_list[pos] = random.choice(chars)
                new_patterns.add("".join(p_list))

            # Method 3: Random pattern with bias toward existing chars
            else:
                new_patterns.add("".join(random.choice(chars) for _ in range(length)))

        # Store new patterns
        for pattern in new_patterns:
            if pattern not in self.patterns:
                mask = self.pattern_to_mask(pattern)
                self.storage.add_pattern(pattern, mask)
                self.patterns[pattern] = 1

        return list(new_patterns)

    def generate_special_patterns(self, length: int, count: int = 20) -> List[str]:
        """Generate patterns that include special characters"""
        patterns = set()
        chars = ['L', 'U', 'D', 'S']

        for _ in range(count):
            # Ensure at least one S (special)
            pattern = [random.choice(chars) for _ in range(length)]

            # Force at least one special char
            if 'S' not in pattern:
                pos = random.randint(0, length - 1)
                pattern[pos] = 'S'

            pattern_str = "".join(pattern)
            patterns.add(pattern_str)

            # Store in DB
            if pattern_str not in self.patterns:
                mask = self.pattern_to_mask(pattern_str)
                self.storage.add_pattern(pattern_str, mask)
                self.patterns[pattern_str] = 1

        return list(patterns)

    def is_weak_pattern(self, pattern: str) -> bool:
        """
        Check if a pattern is considered "weak" (unrealistic for real passwords).

        Weak patterns:
        - All same character type (LLLLLL, UUUUUU, DDDDDD, SSSSSS)
        - Only digits (common but usually handled by brute force)
        - All uppercase (rare for real passwords)
        """
        if len(pattern) < 2:
            return False

        unique_chars = set(pattern)

        # All same type = weak
        if len(unique_chars) == 1:
            return True

        return False

    def is_realistic_pattern(self, pattern: str) -> bool:
        """
        Check if a pattern is realistic (likely to be a real password).

        Realistic patterns have:
        - Mix of at least 2 character types
        - Common structures like: Ulllll, LllllD, UllllDD, etc.
        """
        if len(pattern) < 2:
            return True

        unique_chars = set(pattern)

        # Must have at least 2 different character types
        if len(unique_chars) < 2:
            return False

        return True

    def generate_exhaustive_patterns(self, length: int, skip_weak: bool = True) -> List[str]:
        """
        Generate ALL possible patterns for a given length.
        This is exhaustive - covers every possible combination.

        Length 4: 256 patterns (192 realistic)
        Length 5: 1024 patterns (764 realistic)
        Length 6: 4096 patterns (4092 realistic)
        Length 7: 16384 patterns
        Length 8: 65536 patterns
        Length 10: 1,048,576 patterns (MAX for exhaustive)
        Length 11+: Uses sampling (4^11 = 4M, too much!)

        Args:
            length: Pattern length
            skip_weak: If True, skip weak patterns (all same char type)
        """
        from itertools import product
        chars = ['L', 'U', 'D', 'S']

        # MEMORY LIMIT: For length > 10, use sampling instead of exhaustive
        MAX_EXHAUSTIVE_LENGTH = 10
        MAX_SAMPLED_PATTERNS = 100000  # 100k patterns max for long lengths

        if length > MAX_EXHAUSTIVE_LENGTH:
            return self._generate_sampled_patterns(length, MAX_SAMPLED_PATTERNS, skip_weak)

        all_patterns = []
        skipped = 0

        for combo in product(chars, repeat=length):
            pattern = "".join(combo)

            # Skip weak patterns if requested
            if skip_weak and self.is_weak_pattern(pattern):
                skipped += 1
                continue

            all_patterns.append(pattern)

            # Store in DB if new
            if pattern not in self.patterns:
                mask = self.pattern_to_mask(pattern)
                self.storage.add_pattern(pattern, mask)
                self.patterns[pattern] = 1

        if skipped > 0:
            print(f"[AI] Skipped {skipped} weak patterns for length {length}")

        return all_patterns

    def _generate_sampled_patterns(self, length: int, max_patterns: int, skip_weak: bool = True) -> List[str]:
        """
        Generate patterns in BATCHES for long lengths (> 10).
        Uses sequential iteration through pattern space with tracking.

        For length 15: 4^15 = 1 billion patterns
        We iterate sequentially and track progress with a simple index.
        """
        chars = ['L', 'U', 'D', 'S']

        # Get current progress for this length (stored as pattern index)
        progress_key = f"_progress_{length}"
        current_index = self.storage.load_state(progress_key, 0)
        total_patterns = 4 ** length

        # Check if already exhausted
        if current_index >= total_patterns:
            print(f"[AI] Length {length} EXHAUSTED (all {total_patterns} patterns tried)")
            return []

        print(f"[AI] Length {length}: Generating batch from index {current_index}/{total_patterns} ({current_index*100//total_patterns}%)")

        patterns_list = []
        skipped = 0
        batch_end = min(current_index + max_patterns, total_patterns)

        # Generate patterns sequentially from current index
        for idx in range(current_index, batch_end):
            # Convert index to pattern (base-4 encoding)
            pattern = self._index_to_pattern(idx, length, chars)

            # Skip weak patterns
            if skip_weak and self.is_weak_pattern(pattern):
                skipped += 1
                continue

            patterns_list.append(pattern)

        # Save progress for next batch
        self.storage.save_state(progress_key, batch_end)

        # Store patterns in memory (will be cleared after attack)
        new_count = 0
        for pattern in patterns_list:
            if pattern not in self.patterns:
                mask = self.pattern_to_mask(pattern)
                # Don't save to DB for long lengths (too many!)
                self.patterns[pattern] = 1
                new_count += 1

        progress_pct = batch_end * 100 // total_patterns
        print(f"[AI] Generated {len(patterns_list)} patterns (skipped {skipped} weak), progress: {progress_pct}%")

        return patterns_list

    def generate_patterns_batch_iterator(self, length: int, batch_size: int = 10000, skip_weak: bool = True):
        """
        Generator that yields pattern batches for a given length.
        Memory efficient - only one batch in memory at a time.

        Usage:
            for batch in ai.generate_patterns_batch_iterator(10, batch_size=5000):
                masks = [ai.pattern_to_mask(p) for p in batch]
                hashcat.crack_hcmask(target, masks, ...)

        Args:
            length: Pattern length (e.g., 10 = 4^10 = 1M patterns)
            batch_size: Number of patterns per batch
            skip_weak: Skip weak patterns (all same char type)

        Yields:
            List[str]: Batch of patterns
        """
        chars = ['L', 'U', 'D', 'S']
        total_patterns = 4 ** length

        # Get current progress
        progress_key = f"_progress_{length}"
        current_index = self.storage.load_state(progress_key, 0)

        if current_index >= total_patterns:
            print(f"[AI] Length {length} already EXHAUSTED")
            return

        print(f"[AI] Starting batch iterator for length {length}")
        print(f"[AI] Total patterns: {total_patterns:,}, starting at: {current_index:,}")

        while current_index < total_patterns:
            batch = []
            batch_end = min(current_index + batch_size, total_patterns)
            skipped = 0

            for idx in range(current_index, batch_end):
                pattern = self._index_to_pattern(idx, length, chars)

                if skip_weak and self.is_weak_pattern(pattern):
                    skipped += 1
                    continue

                batch.append(pattern)

            # Update progress BEFORE yielding (in case of interruption)
            current_index = batch_end
            self.storage.save_state(progress_key, current_index)

            progress_pct = current_index * 100 // total_patterns
            print(f"[AI] Batch: {len(batch)} patterns (skipped {skipped}), progress: {progress_pct}%")

            if batch:
                yield batch

        print(f"[AI] Length {length} EXHAUSTED - all {total_patterns:,} patterns processed")

    def get_masks_batch_iterator(self, length: int, batch_size: int = 10000, skip_weak: bool = True):
        """
        Generator that yields hashcat mask batches directly.
        Even more memory efficient - converts patterns to masks on the fly.

        Usage:
            for masks in ai.get_masks_batch_iterator(10, batch_size=5000):
                result = hashcat.crack_hcmask(target, masks, ...)
                if result:
                    break

        Args:
            length: Pattern length
            batch_size: Number of masks per batch
            skip_weak: Skip weak patterns

        Yields:
            List[str]: Batch of hashcat masks
        """
        for pattern_batch in self.generate_patterns_batch_iterator(length, batch_size, skip_weak):
            masks = [self.pattern_to_mask(p) for p in pattern_batch]
            yield masks

    def _index_to_pattern(self, index: int, length: int, chars: List[str]) -> str:
        """Convert numeric index to pattern string (base-4 encoding)."""
        pattern = []
        for _ in range(length):
            pattern.append(chars[index % 4])
            index //= 4
        return "".join(reversed(pattern))

    def clear_patterns_for_length(self, length: int):
        """
        Clear patterns of a specific length from memory.
        Used after attacking to free RAM for next batch.
        """
        to_remove = [p for p in self.patterns.keys() if len(p) == length]
        for p in to_remove:
            del self.patterns[p]
        print(f"[AI] Cleared {len(to_remove)} patterns of length {length} from memory")

    def get_exhaustion_progress(self, length: int) -> Dict:
        """Get exhaustion progress for a length."""
        progress_key = f"_progress_{length}"
        current_index = self.storage.load_state(progress_key, 0)
        total_patterns = 4 ** length

        return {
            "length": length,
            "current_index": current_index,
            "total_patterns": total_patterns,
            "progress_pct": current_index * 100 // total_patterns if total_patterns > 0 else 100,
            "exhausted": current_index >= total_patterns
        }

    def reset_exhaustion_progress(self, length: int = None):
        """Reset exhaustion progress for a length or all lengths."""
        if length:
            progress_key = f"_progress_{length}"
            self.storage.save_state(progress_key, 0)
            print(f"[AI] Reset progress for length {length}")
        else:
            # Reset all
            for l in range(4, 32):
                progress_key = f"_progress_{l}"
                self.storage.save_state(progress_key, 0)
            print(f"[AI] Reset all progress")

    # ========== WORD_ONLY SUBMASK SYSTEM ==========

    # Word_only mask types with their charsets
    WORD_ONLY_TYPES = {
        "lowercase": {"mask_char": "?l", "charset": string.ascii_lowercase, "name": "all lowercase"},
        "capitalized": {"mask_char": "?u?l", "charset": None, "name": "capitalized"},  # Special case
        "uppercase": {"mask_char": "?u", "charset": string.ascii_uppercase, "name": "all uppercase"},
    }

    def get_word_only_submasks_iterator(self, length: int, batch_size: int = 1000, max_keyspace: int = 100_000_000):
        """
        Generator that yields submask batches for word_only category.

        Splits large word_only masks (?l?l?l..., ?u?l?l..., ?u?u?u...) into
        manageable submasks and tracks progress for resume capability.

        For length=10:
        - ?l?l?l?l?l?l?l?l?l?l = 26^10 = 141T -> split into 26^3 * ?l?l?l?l?l?l?l submasks

        Args:
            length: Password length
            batch_size: Number of submasks per batch
            max_keyspace: Max keyspace per submask (for splitting)

        Yields:
            Tuple[List[str], str]: (batch of submasks, current type name)
        """
        for type_key, type_info in self.WORD_ONLY_TYPES.items():
            # Get progress for this type/length combination
            progress_key = f"_word_only_{type_key}_{length}"
            current_index = self.storage.load_state(progress_key, 0)

            # Generate base mask and calculate total submasks
            if type_key == "lowercase":
                base_mask = "?l" * length
                charset = string.ascii_lowercase
            elif type_key == "capitalized":
                if length < 2:
                    continue
                base_mask = "?u" + "?l" * (length - 1)
                charset = string.ascii_lowercase  # Only the ?l parts vary
            elif type_key == "uppercase":
                base_mask = "?u" * length
                charset = string.ascii_uppercase

            # Calculate how many prefix chars to fix to get under max_keyspace
            # keyspace = len(charset)^variable_positions
            # We want: len(charset)^(length - prefix_len) <= max_keyspace
            import math
            charset_size = len(charset)

            if type_key == "capitalized":
                # For capitalized, first char is fixed uppercase, rest are lowercase
                variable_positions = length - 1
                total_keyspace = charset_size ** variable_positions

                # How many positions to fix?
                if total_keyspace > max_keyspace:
                    # Find prefix_len such that charset_size^(variable_positions - prefix_len) <= max_keyspace
                    positions_to_keep = int(math.log(max_keyspace) / math.log(charset_size))
                    prefix_len = variable_positions - positions_to_keep
                    prefix_len = max(1, prefix_len)
                else:
                    prefix_len = 0

                # Generate all possible prefixes
                total_submasks = charset_size ** prefix_len if prefix_len > 0 else 1
            else:
                # For lowercase/uppercase, all positions are same charset
                total_keyspace = charset_size ** length

                if total_keyspace > max_keyspace:
                    positions_to_keep = int(math.log(max_keyspace) / math.log(charset_size))
                    prefix_len = length - positions_to_keep
                    prefix_len = max(1, prefix_len)
                else:
                    prefix_len = 0

                total_submasks = charset_size ** prefix_len if prefix_len > 0 else 1

            # Check if already exhausted
            if current_index >= total_submasks:
                print(f"[AI] word_only/{type_key} length {length} EXHAUSTED ({total_submasks:,} submasks done)")
                continue

            print(f"[AI] word_only/{type_key} length {length}: {total_submasks:,} submasks, starting at {current_index:,}")

            # Generate submasks in batches
            while current_index < total_submasks:
                batch = []
                batch_end = min(current_index + batch_size, total_submasks)

                for idx in range(current_index, batch_end):
                    submask = self._generate_word_only_submask(type_key, length, idx, prefix_len, charset)
                    if submask:
                        batch.append(submask)

                # Save progress
                current_index = batch_end
                self.storage.save_state(progress_key, current_index)

                progress_pct = current_index * 100 // total_submasks
                print(f"[AI] word_only/{type_key}: batch of {len(batch)} submasks, progress: {progress_pct}%")

                if batch:
                    yield batch, type_key

            print(f"[AI] word_only/{type_key} length {length} EXHAUSTED")

    def _generate_word_only_submask(self, type_key: str, length: int, index: int, prefix_len: int, charset: str) -> str:
        """
        Generate a specific submask for word_only by fixing prefix characters.

        Args:
            type_key: lowercase, capitalized, or uppercase
            length: Total password length
            index: Which submask (0 to charset^prefix_len - 1)
            prefix_len: How many characters to fix as prefix
            charset: Character set for the prefix

        Returns:
            Submask string like "abc?l?l?l?l" or "Abc?l?l?l?l"
        """
        if prefix_len == 0:
            # No splitting needed, return base mask
            if type_key == "lowercase":
                return "?l" * length
            elif type_key == "capitalized":
                return "?u" + "?l" * (length - 1)
            elif type_key == "uppercase":
                return "?u" * length

        # Convert index to prefix string (base-N encoding)
        prefix = []
        temp_index = index
        for _ in range(prefix_len):
            prefix.append(charset[temp_index % len(charset)])
            temp_index //= len(charset)
        prefix = "".join(reversed(prefix))

        # Build submask
        if type_key == "lowercase":
            # prefix + ?l for remaining positions
            remaining = length - prefix_len
            return prefix + "?l" * remaining
        elif type_key == "capitalized":
            # First char is uppercase from prefix (converted), rest from prefix + ?l
            first_char = prefix[0].upper()
            rest_prefix = prefix[1:] if len(prefix) > 1 else ""
            remaining = length - 1 - prefix_len
            return first_char + rest_prefix + "?l" * remaining
        elif type_key == "uppercase":
            # prefix (uppercase) + ?u for remaining
            remaining = length - prefix_len
            return prefix + "?u" * remaining

        return None

    def get_word_only_progress(self, length: int) -> Dict:
        """Get word_only exhaustion progress for a length."""
        result = {
            "length": length,
            "types": {},
            "total_progress_pct": 0,
            "exhausted": True
        }

        total_done = 0
        total_submasks = 0

        for type_key in self.WORD_ONLY_TYPES.keys():
            progress_key = f"_word_only_{type_key}_{length}"
            current_index = self.storage.load_state(progress_key, 0)

            # Calculate total submasks for this type (approximate)
            charset_size = 26
            type_total = charset_size ** max(1, length - 7)  # Rough estimate

            result["types"][type_key] = {
                "current": current_index,
                "exhausted": current_index >= type_total
            }

            total_done += current_index
            total_submasks += type_total

            if current_index < type_total:
                result["exhausted"] = False

        if total_submasks > 0:
            result["total_progress_pct"] = total_done * 100 // total_submasks

        return result

    def reset_word_only_progress(self, length: int = None, type_key: str = None):
        """Reset word_only progress."""
        if length and type_key:
            progress_key = f"_word_only_{type_key}_{length}"
            self.storage.save_state(progress_key, 0)
            print(f"[AI] Reset word_only/{type_key} progress for length {length}")
        elif length:
            for tk in self.WORD_ONLY_TYPES.keys():
                progress_key = f"_word_only_{tk}_{length}"
                self.storage.save_state(progress_key, 0)
            print(f"[AI] Reset all word_only progress for length {length}")
        else:
            for l in range(4, 32):
                for tk in self.WORD_ONLY_TYPES.keys():
                    progress_key = f"_word_only_{tk}_{l}"
                    self.storage.save_state(progress_key, 0)
            print(f"[AI] Reset all word_only progress")

    # ========== GENERIC CATEGORY EXHAUSTIVE SUBMASK SYSTEM ==========

    def get_category_submasks_iterator(
        self,
        category: str,
        length: int,
        masks: List[str],
        batch_size: int = 500,
        max_keyspace: int = 100_000_000
    ):
        """
        Generic exhaustive submask iterator for ANY category.

        Takes a list of base masks for a category, splits them into submasks,
        and yields batches with progress tracking for resume capability.

        Progress is tracked as: category/length -> (mask_index, submask_index)

        Args:
            category: Category name (for progress key)
            length: Password length
            masks: List of base masks for this category
            batch_size: Submasks per batch
            max_keyspace: Max keyspace per submask

        Yields:
            Tuple[List[str], int]: (batch of submasks, progress percentage)
        """
        from .hashcat import HashcatWrapper

        # Get or create hashcat instance for split_mask
        hc = HashcatWrapper()

        # Load progress: (mask_index, submask_index within that mask)
        progress_key = f"_cat_{category}_{length}"
        saved_progress = self.storage.load_state(progress_key, {"mask_idx": 0, "sub_idx": 0})

        if isinstance(saved_progress, int):
            # Old format - convert
            saved_progress = {"mask_idx": saved_progress, "sub_idx": 0}

        current_mask_idx = saved_progress.get("mask_idx", 0)
        current_sub_idx = saved_progress.get("sub_idx", 0)

        # Pre-calculate total submasks for progress percentage
        total_submasks = 0
        submasks_per_mask = []
        for mask in masks:
            subs = hc.split_mask(mask, max_keyspace)
            submasks_per_mask.append(subs)
            total_submasks += len(subs)

        if total_submasks == 0:
            print(f"[AI] Category {category} length {length}: no masks to process")
            return

        # Calculate already done
        done_before_start = sum(len(submasks_per_mask[i]) for i in range(current_mask_idx))
        done_before_start += current_sub_idx

        if done_before_start >= total_submasks:
            print(f"[AI] Category {category} length {length} EXHAUSTED ({total_submasks} submasks done)")
            return

        print(f"[AI] Category {category} length {length}: {total_submasks} total submasks")
        print(f"[AI] Resuming from mask {current_mask_idx}, submask {current_sub_idx}")

        # Iterate through masks and their submasks
        batch = []

        for mask_idx in range(current_mask_idx, len(masks)):
            submasks = submasks_per_mask[mask_idx]

            # Start index for this mask
            start_sub_idx = current_sub_idx if mask_idx == current_mask_idx else 0

            for sub_idx in range(start_sub_idx, len(submasks)):
                batch.append(submasks[sub_idx])

                # Yield batch when full
                if len(batch) >= batch_size:
                    # Save progress BEFORE yielding
                    self.storage.save_state(progress_key, {"mask_idx": mask_idx, "sub_idx": sub_idx + 1})

                    # Calculate progress
                    done_now = sum(len(submasks_per_mask[i]) for i in range(mask_idx))
                    done_now += sub_idx + 1
                    progress_pct = done_now * 100 // total_submasks

                    print(f"[AI] {category}: batch of {len(batch)}, progress {progress_pct}%")
                    yield batch, progress_pct
                    batch = []

        # Yield remaining
        if batch:
            self.storage.save_state(progress_key, {"mask_idx": len(masks), "sub_idx": 0})
            print(f"[AI] {category}: final batch of {len(batch)}, progress 100%")
            yield batch, 100

        print(f"[AI] Category {category} length {length} EXHAUSTED")

    def get_category_progress(self, category: str, length: int, masks: List[str], max_keyspace: int = 100_000_000) -> Dict:
        """Get exhaustion progress for a category."""
        from .hashcat import HashcatWrapper
        hc = HashcatWrapper()

        progress_key = f"_cat_{category}_{length}"
        saved_progress = self.storage.load_state(progress_key, {"mask_idx": 0, "sub_idx": 0})

        if isinstance(saved_progress, int):
            saved_progress = {"mask_idx": saved_progress, "sub_idx": 0}

        current_mask_idx = saved_progress.get("mask_idx", 0)
        current_sub_idx = saved_progress.get("sub_idx", 0)

        # Calculate totals
        total_submasks = 0
        for mask in masks:
            subs = hc.split_mask(mask, max_keyspace)
            total_submasks += len(subs)

        # Calculate done
        done = 0
        for i, mask in enumerate(masks):
            subs = hc.split_mask(mask, max_keyspace)
            if i < current_mask_idx:
                done += len(subs)
            elif i == current_mask_idx:
                done += current_sub_idx

        return {
            "category": category,
            "length": length,
            "total_submasks": total_submasks,
            "done": done,
            "progress_pct": done * 100 // total_submasks if total_submasks > 0 else 100,
            "exhausted": done >= total_submasks
        }

    def reset_category_progress(self, category: str = None, length: int = None):
        """Reset category exhaustion progress."""
        if category and length:
            progress_key = f"_cat_{category}_{length}"
            self.storage.save_state(progress_key, {"mask_idx": 0, "sub_idx": 0})
            print(f"[AI] Reset {category} progress for length {length}")
        elif category:
            for l in range(4, 32):
                progress_key = f"_cat_{category}_{l}"
                self.storage.save_state(progress_key, {"mask_idx": 0, "sub_idx": 0})
            print(f"[AI] Reset all {category} progress")
        else:
            # Reset all categories - need category list from loop_cracker
            print(f"[AI] Use reset_category_progress(category, length) for specific reset")

    def _generate_common_structures(self, length: int, count: int) -> List[str]:
        """Generate patterns based on common password structures."""
        patterns = set()

        # Common password structures
        structures = [
            # All lowercase (word)
            'L' * length,
            # Capitalized word
            'U' + 'L' * (length - 1),
            # Word + 1-4 digits
            'L' * (length - 1) + 'D',
            'L' * (length - 2) + 'DD',
            'L' * (length - 3) + 'DDD',
            'L' * (length - 4) + 'DDDD',
            # Capitalized + digits
            'U' + 'L' * (length - 2) + 'D',
            'U' + 'L' * (length - 3) + 'DD',
            'U' + 'L' * (length - 4) + 'DDD',
            # Word + special
            'L' * (length - 1) + 'S',
            'U' + 'L' * (length - 2) + 'S',
            # Word + digit + special
            'L' * (length - 2) + 'DS',
            'U' + 'L' * (length - 3) + 'DS',
            # l33t speak patterns
            'L' + 'D' + 'L' * (length - 2),  # like "a1xxx"
            'U' + 'L' * (length - 3) + 'D' + 'S',  # like "Passw0rd!"
            # All digits (PIN extended)
            'D' * length,
            # Mixed case
            ('UL' * (length // 2 + 1))[:length],
            ('LU' * (length // 2 + 1))[:length],
        ]

        # Add valid structures
        for s in structures:
            if len(s) == length:
                patterns.add(s)

        # Generate variations
        chars = ['L', 'U', 'D', 'S']
        while len(patterns) < count:
            # Pick a base structure and mutate it
            if patterns:
                base = random.choice(list(patterns))
            else:
                base = 'L' * length

            mutated = list(base)
            # Mutate 1-2 positions
            for _ in range(random.randint(1, 2)):
                pos = random.randint(0, length - 1)
                mutated[pos] = random.choice(chars)
            patterns.add("".join(mutated))

        return list(patterns)[:count]

    def generate_all_patterns(self, length: int, count: int = 100) -> List[str]:
        """
        Generate random patterns directly (no password generation needed).
        This is much faster than generating passwords and extracting patterns.
        """
        patterns = set()
        chars = ['L', 'U', 'D', 'S']

        # Common pattern templates based on real password structures
        templates = [
            # All same type
            lambda l: 'L' * l,
            lambda l: 'U' * l,
            lambda l: 'D' * l,
            # Capitalized word
            lambda l: 'U' + 'L' * (l - 1),
            # Word + digits
            lambda l: 'L' * (l - 2) + 'DD',
            lambda l: 'L' * (l - 1) + 'D',
            # Word + special
            lambda l: 'L' * (l - 1) + 'S',
            lambda l: 'L' * (l - 2) + 'DS',
            # Capitalized + digit
            lambda l: 'U' + 'L' * (l - 2) + 'D',
            lambda l: 'U' + 'L' * (l - 3) + 'DD',
            # Mixed case
            lambda l: 'U' + 'L' * (l - 2) + 'U',
            lambda l: 'L' + 'U' * (l - 1),
            # With special in middle
            lambda l: 'L' * (l // 2) + 'S' + 'L' * (l - l // 2 - 1),
            lambda l: 'U' + 'L' * (l // 2 - 1) + 'S' + 'D' * (l - l // 2 - 1),
        ]

        # Add template patterns
        for template in templates:
            try:
                p = template(length)
                if len(p) == length:
                    patterns.add(p)
            except:
                pass

        # Generate random patterns
        for _ in range(count):
            # Weighted random - favor L and D over U and S
            weights = [0.4, 0.25, 0.25, 0.1]  # L, U, D, S
            pattern = "".join(random.choices(chars, weights=weights, k=length))
            patterns.add(pattern)

        # Store all new patterns
        new_count = 0
        for pattern in patterns:
            if pattern not in self.patterns:
                mask = self.pattern_to_mask(pattern)
                self.storage.add_pattern(pattern, mask)
                self.patterns[pattern] = 1
                new_count += 1

        return list(patterns)

    # ========== HASHCAT INTEGRATION ==========

    def get_top_patterns(self, length: int = None, limit: int = 50) -> List[Dict]:
        """Get top patterns for hashcat"""
        if length:
            patterns = {p: c for p, c in self.patterns.items() if len(p) == length}
        else:
            patterns = self.patterns

        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {"pattern": p, "mask": self.pattern_to_mask(p), "count": c, "length": len(p)}
            for p, c in sorted_patterns
        ]

    def get_top_masks(self, length: int = None, limit: int = 50) -> List[str]:
        """Get hashcat masks for top patterns"""
        top = self.get_top_patterns(length, limit)
        return [p["mask"] for p in top]

    def write_hcmask_file(self, filepath: str, length: int = None, limit: int = 100) -> int:
        """Write .hcmask file with all patterns for hashcat"""
        masks = self.get_top_masks(length, limit)

        # Add default masks if not enough learned
        default_masks = [
            "?l" * (length or 8),  # all lowercase
            "?u" * (length or 8),  # all uppercase
            "?d" * (length or 8),  # all digits
            "?u" + "?l" * ((length or 8) - 1),  # Capitalized
        ]

        for m in default_masks:
            if m not in masks:
                masks.append(m)

        with open(filepath, "w") as f:
            for mask in masks:
                f.write(mask + "\n")

        return len(masks)

    # ========== STATS ==========

    def get_stats(self) -> Dict:
        """Get learning statistics"""
        return {
            "total_learned": self.total_learned,
            "generation": self.generation,
            "unique_patterns": len(self.patterns),
            "bigram_pairs": sum(len(v) for v in self.bigrams.values()),
            "trigram_pairs": sum(len(v) for v in self.trigrams.values()),
            "population_size": len(self.population),
            "top_patterns": self.get_top_patterns(limit=10)
        }

    def reset(self):
        """Reset all learning state"""
        self.bigrams = defaultdict(lambda: defaultdict(int))
        self.trigrams = defaultdict(lambda: defaultdict(int))
        self.position_weights = defaultdict(lambda: defaultdict(int))
        self.patterns = defaultdict(int)
        self.total_learned = 0
        self.generation = 0
        self.population = []
        self._save_state()


# Singleton
_ai: Optional[LearningPasswordAI] = None

def get_ai(data_dir: Optional[str] = None) -> LearningPasswordAI:
    """Get or create AI instance"""
    global _ai
    if _ai is None:
        _ai = LearningPasswordAI(data_dir)
    return _ai
