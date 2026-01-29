"""
Hashcat GPU Operations - Start/Stop/Status/Crack
"""
import os
import subprocess
import tempfile
import shutil
import asyncio
from typing import Optional, Dict, List, Callable
from pathlib import Path
from enum import Enum


class HashType(Enum):
    """Supported hash types with hashcat mode codes"""
    MD5 = 0
    SHA1 = 100
    SHA256 = 1400
    SHA512 = 1700
    NTLM = 1000
    BCRYPT = 3200
    KECCAK256 = 17800  # Ethereum


class HashcatStatus(Enum):
    """Hashcat process status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CRACKED = "cracked"
    EXHAUSTED = "exhausted"
    ERROR = "error"


class HashcatGPU:
    """Hashcat GPU wrapper with start/stop/status control"""

    def __init__(self, hashcat_path: Optional[str] = None):
        self.hashcat_path = hashcat_path or self._find_hashcat()
        self.process: Optional[subprocess.Popen] = None
        self.status = HashcatStatus.IDLE
        self.current_hash: Optional[str] = None
        self.current_mask: Optional[str] = None
        self.result: Optional[str] = None
        self.temp_dir = tempfile.mkdtemp(prefix="nanopy_dual_")
        self.potfile = os.path.join(self.temp_dir, "cracked.pot")
        self.output_file = os.path.join(self.temp_dir, "output.txt")
        self.hcmask_file = os.path.join(self.temp_dir, "patterns.hcmask")

        # Stats
        self.masks_tested: int = 0
        self.masks_exhausted: int = 0
        self.current_keyspace: int = 0
        self.current_progress: int = 0

        # Callbacks
        self.on_cracked: Optional[Callable[[str, str], None]] = None
        self.on_status: Optional[Callable[[str, Dict], None]] = None

    def _find_hashcat(self) -> str:
        """Find hashcat binary"""
        # Common locations
        paths = [
            "hashcat",
            "hashcat.exe",
            "/usr/bin/hashcat",
            "/usr/local/bin/hashcat",
            "C:\\hashcat\\hashcat.exe",
            "C:\\Program Files\\hashcat\\hashcat.exe",
            os.path.expanduser("~/hashcat/hashcat.bin"),
        ]

        for p in paths:
            if shutil.which(p):
                return p

        # Try just "hashcat" and hope it's in PATH
        return "hashcat"

    def is_available(self) -> bool:
        """Check if hashcat is available"""
        try:
            result = subprocess.run(
                [self.hashcat_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Get hashcat version"""
        try:
            result = subprocess.run(
                [self.hashcat_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return None

    def get_devices(self) -> List[Dict]:
        """List available GPU devices"""
        try:
            result = subprocess.run(
                [self.hashcat_path, "-I"],
                capture_output=True, text=True, timeout=10
            )
            # Parse device info (simplified)
            devices = []
            lines = result.stdout.split("\n")
            current_device = {}
            for line in lines:
                if "Device ID" in line or "Backend Device" in line:
                    if current_device:
                        devices.append(current_device)
                    current_device = {"raw": line}
                elif current_device:
                    current_device["raw"] += "\n" + line
            if current_device:
                devices.append(current_device)
            return devices
        except Exception:
            return []

    def hash_string(self, password: str, hash_type: HashType = HashType.SHA256) -> str:
        """Generate hash from password"""
        import hashlib

        if hash_type == HashType.MD5:
            return hashlib.md5(password.encode()).hexdigest()
        elif hash_type == HashType.SHA1:
            return hashlib.sha1(password.encode()).hexdigest()
        elif hash_type == HashType.SHA256:
            return hashlib.sha256(password.encode()).hexdigest()
        elif hash_type == HashType.SHA512:
            return hashlib.sha512(password.encode()).hexdigest()
        else:
            return hashlib.sha256(password.encode()).hexdigest()

    # Character sets for mask expansion
    CHARSET = {
        'l': 'abcdefghijklmnopqrstuvwxyz',
        'u': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'd': '0123456789',
        's': '!@#$%^&*()_+-=[]{}|;:,.<>?',
    }

    def calc_keyspace(self, mask: str) -> int:
        """
        Calculate keyspace (number of combinations) for a mask.

        ?l = 26, ?u = 26, ?d = 10, ?s = 33, ?a = 95
        """
        keyspace = 1
        i = 0
        while i < len(mask):
            if mask[i] == '?':
                if i + 1 < len(mask):
                    c = mask[i + 1]
                    if c == 'l':
                        keyspace *= 26
                    elif c == 'u':
                        keyspace *= 26
                    elif c == 'd':
                        keyspace *= 10
                    elif c == 's':
                        keyspace *= 33
                    elif c == 'a':
                        keyspace *= 95
                    else:
                        keyspace *= 95  # default
                    i += 2
                else:
                    i += 1
            else:
                i += 1  # literal character
        return keyspace

    def split_mask(self, mask: str, max_keyspace: int = 100_000_000) -> List[str]:
        """
        Split a large mask into smaller sub-masks by fixing prefix characters.

        Example: ?l?l?l?l?l?l?l?l (208B) with max_keyspace=100M
        -> ['a?l?l?l?l?l?l?l', 'b?l?l?l?l?l?l?l', ..., 'z?l?l?l?l?l?l?l']
        Each sub-mask has keyspace 26^7 = 8B, still too big
        -> ['aa?l?l?l?l?l?l', 'ab?l?l?l?l?l?l', ..., 'zz?l?l?l?l?l?l']
        Each has 26^6 = 308M, still too big
        -> ['aaa?l?l?l?l?l', ...] = 26^5 = 11M, OK!

        Returns list of sub-masks, each with keyspace <= max_keyspace
        """
        keyspace = self.calc_keyspace(mask)

        # If already small enough, return as-is
        if keyspace <= max_keyspace:
            return [mask]

        # Find first variable position (?x)
        i = 0
        while i < len(mask):
            if mask[i] == '?' and i + 1 < len(mask):
                char_type = mask[i + 1]
                if char_type in self.CHARSET:
                    # Split at this position
                    prefix = mask[:i]
                    suffix = mask[i + 2:]  # Skip ?x
                    charset = self.CHARSET[char_type]

                    sub_masks = []
                    for c in charset:
                        sub_mask = prefix + c + suffix
                        # Recursively split if still too big
                        sub_masks.extend(self.split_mask(sub_mask, max_keyspace))

                    return sub_masks
                else:
                    i += 2
            else:
                i += 1

        # No variable found, return as-is
        return [mask]

    def split_masks_batch(self, masks: List[str], max_keyspace: int = 100_000_000) -> List[str]:
        """
        Split all masks that exceed max_keyspace into smaller sub-masks.

        Args:
            masks: List of masks to process
            max_keyspace: Maximum keyspace per mask

        Returns:
            List of masks, all with keyspace <= max_keyspace
        """
        result = []
        for mask in masks:
            keyspace = self.calc_keyspace(mask)
            if keyspace > max_keyspace:
                sub_masks = self.split_mask(mask, max_keyspace)
                print(f"[HC] Split {mask} (keyspace {keyspace:,}) into {len(sub_masks)} sub-masks")
                result.extend(sub_masks)
            else:
                result.append(mask)
        return result

    def _write_hash_file(self, hash_value: str) -> str:
        """Write hash to temp file"""
        hash_file = os.path.join(self.temp_dir, "target.hash")
        with open(hash_file, "w") as f:
            f.write(hash_value)
        return hash_file

    def _build_command(
        self,
        hash_file: str,
        hash_type: HashType,
        attack_mode: int = 3,
        mask: Optional[str] = None,
        wordlist: Optional[str] = None,
        extra_args: List[str] = None
    ) -> List[str]:
        """Build hashcat command"""
        cmd = [
            self.hashcat_path,
            "-m", str(hash_type.value),
            "-a", str(attack_mode),
            "--potfile-path", self.potfile,
            "-o", self.output_file,
            "--outfile-format", "2",  # Plain password only
            "-w", "3",  # Workload profile (high)
            "--quiet",
        ]

        cmd.append(hash_file)

        if attack_mode == 0 and wordlist:
            # Dictionary attack
            cmd.append(wordlist)
        elif attack_mode == 3:
            # Mask attack
            if mask:
                cmd.append(mask)
            else:
                cmd.append("?a?a?a?a?a?a?a?a")  # Default 8 chars

        if extra_args:
            cmd.extend(extra_args)

        return cmd

    def crack_mask(
        self,
        hash_value: str,
        mask: str,
        hash_type: HashType = HashType.SHA256,
        timeout: int = 300
    ) -> Optional[str]:
        """Crack hash with single mask (blocking)"""
        hash_file = self._write_hash_file(hash_value)
        cmd = self._build_command(hash_file, hash_type, attack_mode=3, mask=mask)

        self.status = HashcatStatus.RUNNING
        self.current_hash = hash_value
        self.current_mask = mask

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            if os.path.exists(self.output_file):
                with open(self.output_file) as f:
                    password = f.read().strip()
                    if password:
                        self.status = HashcatStatus.CRACKED
                        self.result = password
                        if self.on_cracked:
                            self.on_cracked(hash_value, password)
                        return password

            self.status = HashcatStatus.EXHAUSTED
            return None

        except subprocess.TimeoutExpired:
            self.status = HashcatStatus.EXHAUSTED
            return None
        except Exception as e:
            self.status = HashcatStatus.ERROR
            return None

    def crack_hcmask(
        self,
        hash_value: str,
        masks: List[str],
        hash_type: HashType = HashType.SHA256,
        timeout: int = 600
    ) -> Optional[str]:
        """Crack hash with multiple masks from .hcmask file (blocking)"""
        # Write masks to file
        with open(self.hcmask_file, "w") as f:
            for mask in masks:
                f.write(mask + "\n")

        hash_file = self._write_hash_file(hash_value)
        cmd = self._build_command(
            hash_file, hash_type, attack_mode=3, mask=self.hcmask_file
        )

        self.status = HashcatStatus.RUNNING
        self.current_hash = hash_value
        self.current_mask = f"{len(masks)} masks"

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            if os.path.exists(self.output_file):
                with open(self.output_file) as f:
                    password = f.read().strip()
                    if password:
                        self.status = HashcatStatus.CRACKED
                        self.result = password
                        if self.on_cracked:
                            self.on_cracked(hash_value, password)
                        return password

            self.status = HashcatStatus.EXHAUSTED
            return None

        except subprocess.TimeoutExpired:
            self.status = HashcatStatus.EXHAUSTED
            return None
        except Exception as e:
            self.status = HashcatStatus.ERROR
            return None

    def crack_wordlist(
        self,
        hash_value: str,
        wordlist: str,
        hash_type: HashType = HashType.SHA256,
        timeout: int = 300
    ) -> Optional[str]:
        """Crack hash with wordlist (blocking)"""
        hash_file = self._write_hash_file(hash_value)
        cmd = self._build_command(
            hash_file, hash_type, attack_mode=0, wordlist=wordlist
        )

        self.status = HashcatStatus.RUNNING
        self.current_hash = hash_value

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            if os.path.exists(self.output_file):
                with open(self.output_file) as f:
                    password = f.read().strip()
                    if password:
                        self.status = HashcatStatus.CRACKED
                        self.result = password
                        if self.on_cracked:
                            self.on_cracked(hash_value, password)
                        return password

            self.status = HashcatStatus.EXHAUSTED
            return None

        except subprocess.TimeoutExpired:
            self.status = HashcatStatus.EXHAUSTED
            return None
        except Exception as e:
            self.status = HashcatStatus.ERROR
            return None

    def crack_masks_sequential(
        self,
        hash_value: str,
        masks: List[str],
        hash_type: HashType = HashType.SHA256,
        timeout_per_mask: int = 0,
        max_keyspace: int = 100_000_000,
        on_mask_done: Optional[Callable[[str, int, bool], None]] = None
    ) -> Optional[str]:
        """
        Crack hash by testing each mask SEQUENTIALLY until exhausted.

        This ensures each mask is fully tested before moving to the next.
        Large masks are automatically split into smaller sub-masks.

        Args:
            hash_value: Target hash
            masks: List of masks to try
            hash_type: Hash type
            timeout_per_mask: Timeout per mask (0 = no timeout, wait for exhaustion)
            max_keyspace: Split masks with keyspace > this (default 100M)
            on_mask_done: Callback(mask, keyspace, exhausted) after each mask

        Returns:
            Password if found, None otherwise
        """
        hash_file = self._write_hash_file(hash_value)
        self.masks_tested = 0
        self.masks_exhausted = 0

        # Split large masks into manageable sub-masks
        if max_keyspace > 0:
            masks = self.split_masks_batch(masks, max_keyspace)

        total_masks = len(masks)

        for mask in masks:
            # Calculate keyspace
            keyspace = self.calc_keyspace(mask)
            self.current_keyspace = keyspace
            self.current_mask = mask

            self.masks_tested += 1
            print(f"[HC] Testing mask {self.masks_tested}/{total_masks}: {mask} (keyspace: {keyspace:,})")

            # Build command without --quiet to see progress
            cmd = [
                self.hashcat_path,
                "-m", str(hash_type.value),
                "-a", "3",
                "--potfile-path", self.potfile,
                "-o", self.output_file,
                "--outfile-format", "2",
                "-w", "3",
                hash_file,
                mask
            ]

            self.status = HashcatStatus.RUNNING

            try:
                if timeout_per_mask > 0:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=timeout_per_mask
                    )
                    exhausted = result.returncode == 1  # hashcat returns 1 when exhausted
                else:
                    # No timeout - wait for hashcat to finish (exhaust the mask)
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    exhausted = True

                # Check result
                if os.path.exists(self.output_file):
                    with open(self.output_file) as f:
                        password = f.read().strip()
                        if password:
                            self.status = HashcatStatus.CRACKED
                            self.result = password
                            print(f"[HC] CRACKED! {password}")
                            if self.on_cracked:
                                self.on_cracked(hash_value, password)
                            return password

                if exhausted:
                    self.masks_exhausted += 1
                    print(f"[HC] Mask exhausted: {mask}")

                if on_mask_done:
                    on_mask_done(mask, keyspace, exhausted)

            except subprocess.TimeoutExpired:
                print(f"[HC] Timeout on mask: {mask}")
                if on_mask_done:
                    on_mask_done(mask, keyspace, False)

            except Exception as e:
                print(f"[HC] Error on mask {mask}: {e}")

        self.status = HashcatStatus.EXHAUSTED
        print(f"[HC] All {self.masks_tested} masks tested, {self.masks_exhausted} exhausted")
        return None

    # ========== ASYNC OPERATIONS ==========

    async def start_crack_async(
        self,
        hash_value: str,
        masks: List[str],
        hash_type: HashType = HashType.SHA256
    ):
        """Start hashcat process asynchronously (non-blocking)"""
        # Write masks
        with open(self.hcmask_file, "w") as f:
            for mask in masks:
                f.write(mask + "\n")

        hash_file = self._write_hash_file(hash_value)
        cmd = self._build_command(
            hash_file, hash_type, attack_mode=3, mask=self.hcmask_file
        )

        self.status = HashcatStatus.RUNNING
        self.current_hash = hash_value
        self.current_mask = f"{len(masks)} masks"
        self.result = None

        # Clear output file
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def check_result(self) -> Optional[str]:
        """Check if password was found (non-blocking)"""
        if os.path.exists(self.output_file):
            with open(self.output_file) as f:
                password = f.read().strip()
                if password:
                    self.status = HashcatStatus.CRACKED
                    self.result = password
                    return password
        return None

    def is_running(self) -> bool:
        """Check if hashcat is still running"""
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self):
        """Stop hashcat process"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        self.status = HashcatStatus.IDLE

    def pause(self):
        """Pause hashcat (send 'p' to stdin) - requires interactive mode"""
        # Note: This requires hashcat to be running in interactive mode
        pass

    def resume(self):
        """Resume hashcat"""
        pass

    def get_status(self) -> Dict:
        """Get current status"""
        return {
            "status": self.status.value,
            "hash": self.current_hash,
            "mask": self.current_mask,
            "result": self.result,
            "running": self.is_running(),
            "available": self.is_available(),
            "version": self.get_version(),
            "masks_tested": self.masks_tested,
            "masks_exhausted": self.masks_exhausted,
            "current_keyspace": self.current_keyspace
        }

    def cleanup(self):
        """Clean up temp files"""
        self.stop()
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def __del__(self):
        self.cleanup()


# Singleton
_hashcat: Optional[HashcatGPU] = None

def get_hashcat(hashcat_path: Optional[str] = None) -> HashcatGPU:
    """Get or create hashcat instance"""
    global _hashcat
    if _hashcat is None:
        _hashcat = HashcatGPU(hashcat_path)
    return _hashcat
