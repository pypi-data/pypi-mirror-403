"""
Storage module for patterns database (LevelDB + SQLite)
"""
import os
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    import plyvel
    HAS_PLYVEL = True
except ImportError:
    HAS_PLYVEL = False


class PatternStorage:
    """Dual storage: LevelDB (fast) + SQLite (queryable)"""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.nanopy-dual")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # LevelDB for fast pattern access
        self.ldb_path = self.data_dir / "patterns.ldb"
        self.ldb = None
        if HAS_PLYVEL:
            self.ldb = plyvel.DB(str(self.ldb_path), create_if_missing=True)

        # SQLite for queries
        self.db_path = self.data_dir / "patterns.db"
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite tables"""
        cursor = self.conn.cursor()

        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE NOT NULL,
                mask TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                length INTEGER,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'learned'
            )
        """)

        # Cracked passwords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cracked (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT NOT NULL,
                hash_type TEXT,
                password TEXT NOT NULL,
                pattern TEXT,
                cracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                method TEXT
            )
        """)

        # Learning state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_hash TEXT,
                hash_type TEXT,
                status TEXT DEFAULT 'running',
                patterns_tried INTEGER DEFAULT 0,
                passwords_generated INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                result TEXT
            )
        """)

        # Target tracking table - track pattern evolution per target
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crack_count INTEGER DEFAULT 0,
                notes TEXT
            )
        """)

        # Pattern history for each target
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS target_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT NOT NULL,
                hash TEXT NOT NULL,
                password TEXT NOT NULL,
                pattern TEXT NOT NULL,
                length INTEGER,
                has_upper INTEGER DEFAULT 0,
                has_lower INTEGER DEFAULT 0,
                has_digit INTEGER DEFAULT 0,
                has_special INTEGER DEFAULT 0,
                cracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (target_id) REFERENCES targets(target_id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern ON patterns(pattern)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON cracked(hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_target ON targets(target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_patterns ON target_patterns(target_id)")

        self.conn.commit()

    # ========== PATTERN METHODS ==========

    def add_pattern(self, pattern: str, mask: str) -> int:
        """Add or update a pattern"""
        cursor = self.conn.cursor()

        # Check if exists
        cursor.execute("SELECT id, count FROM patterns WHERE pattern = ?", (pattern,))
        row = cursor.fetchone()

        if row:
            # Update count
            cursor.execute("""
                UPDATE patterns SET count = count + 1, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (row[0],))
            pattern_id = row[0]
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO patterns (pattern, mask, length) VALUES (?, ?, ?)
            """, (pattern, mask, len(pattern)))
            pattern_id = cursor.lastrowid

        self.conn.commit()

        # Also store in LevelDB
        if self.ldb:
            key = f"pattern:{pattern}".encode()
            data = json.dumps({"mask": mask, "count": row[1] + 1 if row else 1})
            self.ldb.put(key, data.encode())

        return pattern_id

    def get_patterns(self, limit: int = 100, min_count: int = 1) -> List[Dict]:
        """Get top patterns sorted by count"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT pattern, mask, count, length, status
            FROM patterns
            WHERE count >= ?
            ORDER BY count DESC
            LIMIT ?
        """, (min_count, limit))

        return [
            {"pattern": r[0], "mask": r[1], "count": r[2], "length": r[3], "status": r[4]}
            for r in cursor.fetchall()
        ]

    def get_masks_for_length(self, length: int, limit: int = 50, skip_weak: bool = True) -> List[str]:
        """
        Get hashcat masks for a specific length.

        Args:
            length: Pattern length
            limit: Max masks to return
            skip_weak: Skip weak patterns (all same char: ?l?l?l?l, ?u?u?u?u, ?d?d?d?d, ?s?s?s?s)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT mask, pattern FROM patterns
            WHERE length = ?
            ORDER BY count DESC
            LIMIT ?
        """, (length, limit * 2 if skip_weak else limit))  # Get more to account for filtered

        masks = []
        for r in cursor.fetchall():
            mask, pattern = r[0], r[1]

            # Skip weak patterns (all same char type)
            if skip_weak and pattern:
                unique_chars = set(pattern)
                if len(unique_chars) == 1:
                    continue  # Skip LLLLLL, UUUUUU, DDDDDD, SSSSSS

            masks.append(mask)
            if len(masks) >= limit:
                break

        return masks

    def get_all_masks(self, limit: int = 1000) -> List[str]:
        """Get all masks sorted by popularity"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT mask FROM patterns
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        return [r[0] for r in cursor.fetchall()]

    def update_pattern_status(self, pattern: str, status: str):
        """Update pattern status (learned, trying, tried, found)"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE patterns SET status = ? WHERE pattern = ?", (status, pattern))
        self.conn.commit()

    def get_pattern_count(self) -> int:
        """Get total number of patterns"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patterns")
        return cursor.fetchone()[0]

    # ========== CRACKED PASSWORDS ==========

    def add_cracked(self, hash_val: str, password: str, hash_type: str = "sha256",
                    pattern: str = None, method: str = "hashcat"):
        """Store a cracked password"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO cracked (hash, hash_type, password, pattern, method)
            VALUES (?, ?, ?, ?, ?)
        """, (hash_val, hash_type, password, pattern, method))
        self.conn.commit()

        # Also in LevelDB
        if self.ldb:
            key = f"cracked:{hash_val}".encode()
            self.ldb.put(key, password.encode())

    def get_cracked(self, hash_val: str) -> Optional[str]:
        """Check if hash is already cracked"""
        # Try LevelDB first (faster)
        if self.ldb:
            key = f"cracked:{hash_val}".encode()
            val = self.ldb.get(key)
            if val:
                return val.decode()

        # Fallback to SQLite
        cursor = self.conn.cursor()
        cursor.execute("SELECT password FROM cracked WHERE hash = ?", (hash_val,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_cracked_list(self, limit: int = 100) -> List[Dict]:
        """Get list of cracked passwords"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT hash, password, hash_type, pattern, method, cracked_at
            FROM cracked
            ORDER BY cracked_at DESC
            LIMIT ?
        """, (limit,))
        return [
            {"hash": r[0], "password": r[1], "hash_type": r[2],
             "pattern": r[3], "method": r[4], "cracked_at": r[5]}
            for r in cursor.fetchall()
        ]

    # ========== LEARNING STATE ==========

    def save_state(self, key: str, value: Any):
        """Save learning state"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO learning_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, json.dumps(value)))
        self.conn.commit()

        if self.ldb:
            self.ldb.put(f"state:{key}".encode(), json.dumps(value).encode())

    def load_state(self, key: str, default: Any = None) -> Any:
        """Load learning state"""
        if self.ldb:
            val = self.ldb.get(f"state:{key}".encode())
            if val:
                return json.loads(val.decode())

        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM learning_state WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return default

    # ========== SESSIONS ==========

    def create_session(self, target_hash: str, hash_type: str) -> int:
        """Create a new cracking session"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (target_hash, hash_type)
            VALUES (?, ?)
        """, (target_hash, hash_type))
        self.conn.commit()
        return cursor.lastrowid

    def update_session(self, session_id: int, **kwargs):
        """Update session stats"""
        cursor = self.conn.cursor()
        sets = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        cursor.execute(f"UPDATE sessions SET {sets} WHERE id = ?",
                      (*kwargs.values(), session_id))
        self.conn.commit()

    def finish_session(self, session_id: int, result: str):
        """Mark session as finished"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions SET status = 'finished', finished_at = CURRENT_TIMESTAMP, result = ?
            WHERE id = ?
        """, (result, session_id))
        self.conn.commit()

    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get session info"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "target_hash": row[1], "hash_type": row[2],
                "status": row[3], "patterns_tried": row[4], "passwords_generated": row[5],
                "started_at": row[6], "finished_at": row[7], "result": row[8]
            }
        return None

    # ========== TARGET TRACKING ==========

    def add_target(self, target_id: str, name: str = None) -> str:
        """Add or get a target for tracking"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT target_id FROM targets WHERE target_id = ?", (target_id,))
        row = cursor.fetchone()

        if not row:
            cursor.execute("""
                INSERT INTO targets (target_id, name) VALUES (?, ?)
            """, (target_id, name or target_id))
            self.conn.commit()

        return target_id

    def track_cracked_pattern(self, target_id: str, hash_val: str, password: str, pattern: str):
        """Track a cracked password pattern for a target"""
        # Ensure target exists
        self.add_target(target_id)

        # Analyze password characteristics
        has_upper = 1 if any(c.isupper() for c in password) else 0
        has_lower = 1 if any(c.islower() for c in password) else 0
        has_digit = 1 if any(c.isdigit() for c in password) else 0
        has_special = 1 if any(not c.isalnum() for c in password) else 0

        cursor = self.conn.cursor()

        # Add to pattern history
        cursor.execute("""
            INSERT INTO target_patterns
            (target_id, hash, password, pattern, length, has_upper, has_lower, has_digit, has_special)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (target_id, hash_val, password, pattern, len(password),
              has_upper, has_lower, has_digit, has_special))

        # Update target stats
        cursor.execute("""
            UPDATE targets SET crack_count = crack_count + 1, last_seen = CURRENT_TIMESTAMP
            WHERE target_id = ?
        """, (target_id,))

        self.conn.commit()

    def get_target_history(self, target_id: str) -> List[Dict]:
        """Get pattern evolution history for a target"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT hash, password, pattern, length, has_upper, has_lower, has_digit, has_special, cracked_at
            FROM target_patterns
            WHERE target_id = ?
            ORDER BY cracked_at ASC
        """, (target_id,))

        return [
            {
                "hash": r[0][:16] + "...",
                "password": r[1],
                "pattern": r[2],
                "length": r[3],
                "has_upper": bool(r[4]),
                "has_lower": bool(r[5]),
                "has_digit": bool(r[6]),
                "has_special": bool(r[7]),
                "cracked_at": r[8]
            }
            for r in cursor.fetchall()
        ]

    def predict_next_pattern(self, target_id: str) -> Dict:
        """
        Predict the next likely pattern for a target based on their history.
        Returns suggested patterns to try first.
        """
        history = self.get_target_history(target_id)

        if not history:
            return {"patterns": [], "prediction": "No history"}

        # Analyze evolution
        last = history[-1]
        predictions = []

        # Base pattern with variations
        base_pattern = last["pattern"]
        base_length = last["length"]

        # Prediction 1: Same pattern, longer
        if base_length < 16:
            predictions.append({
                "pattern": base_pattern + "D",
                "reason": "Add digit at end"
            })
            predictions.append({
                "pattern": base_pattern + "S",
                "reason": "Add special at end"
            })
            predictions.append({
                "pattern": base_pattern + "DD",
                "reason": "Add 2 digits at end"
            })

        # Prediction 2: Same structure, add complexity
        if not last["has_special"]:
            # They don't use special chars yet, predict they might add one
            predictions.append({
                "pattern": base_pattern[:-1] + "S" if len(base_pattern) > 1 else "S",
                "reason": "Replace last char with special"
            })
            predictions.append({
                "pattern": "S" + base_pattern,
                "reason": "Add special at start"
            })

        if not last["has_upper"] and last["has_lower"]:
            # Convert first lowercase to uppercase (capitalize)
            new_pattern = "U" + base_pattern[1:] if base_pattern.startswith("L") else base_pattern
            predictions.append({
                "pattern": new_pattern,
                "reason": "Capitalize first letter"
            })

        # Prediction 3: Look at evolution trend
        if len(history) >= 2:
            prev = history[-2]
            length_increase = last["length"] - prev["length"]

            if length_increase > 0:
                # They're increasing length, predict more
                predictions.append({
                    "pattern": base_pattern + ("D" * length_increase),
                    "reason": f"Continue +{length_increase} length trend"
                })

            # Check if they added complexity
            if last["has_special"] and not prev["has_special"]:
                predictions.append({
                    "pattern": base_pattern + "S",
                    "reason": "Continue adding specials trend"
                })

        return {
            "target_id": target_id,
            "last_pattern": base_pattern,
            "last_length": base_length,
            "history_count": len(history),
            "predictions": predictions[:10]  # Top 10 predictions
        }

    def get_all_targets(self, limit: int = 100) -> List[Dict]:
        """Get all tracked targets"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT target_id, name, crack_count, created_at, last_seen
            FROM targets
            ORDER BY last_seen DESC
            LIMIT ?
        """, (limit,))

        return [
            {
                "target_id": r[0],
                "name": r[1],
                "crack_count": r[2],
                "created_at": r[3],
                "last_seen": r[4]
            }
            for r in cursor.fetchall()
        ]

    def get_target_suggested_masks(self, target_id: str, length: int = None) -> List[str]:
        """
        Get suggested hashcat masks based on target's pattern history.
        These should be tried FIRST before generic patterns.
        """
        prediction = self.predict_next_pattern(target_id)
        masks = []

        # Import pattern_to_mask from learning_ai
        def pattern_to_mask(pattern: str) -> str:
            mapping = {'L': '?l', 'U': '?u', 'D': '?d', 'S': '?s'}
            return "".join(mapping.get(c, c) for c in pattern)

        for pred in prediction.get("predictions", []):
            p = pred["pattern"]
            if length is None or len(p) == length:
                masks.append(pattern_to_mask(p))

        # Also add variations of their historical patterns
        history = self.get_target_history(target_id)
        for h in history[-5:]:  # Last 5 patterns
            p = h["pattern"]
            if length is None or len(p) == length:
                mask = pattern_to_mask(p)
                if mask not in masks:
                    masks.append(mask)

        return masks

    # ========== STATS ==========

    def get_stats(self) -> Dict:
        """Get storage statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patterns")
        patterns = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM cracked")
        cracked = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'running'")
        running = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(count) FROM patterns")
        total_learned = cursor.fetchone()[0] or 0

        return {
            "patterns": patterns,
            "cracked": cracked,
            "running_sessions": running,
            "total_learned": total_learned,
            "leveldb": HAS_PLYVEL and self.ldb is not None
        }

    def close(self):
        """Close connections"""
        self.conn.close()
        if self.ldb:
            self.ldb.close()


# Singleton instance
_storage: Optional[PatternStorage] = None

def get_storage(data_dir: Optional[str] = None) -> PatternStorage:
    """Get or create storage instance"""
    global _storage
    if _storage is None:
        _storage = PatternStorage(data_dir)
    return _storage
