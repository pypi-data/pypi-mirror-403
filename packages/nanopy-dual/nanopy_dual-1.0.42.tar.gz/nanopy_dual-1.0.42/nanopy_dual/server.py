"""
Web Server API for nanopy-dual
"""
import os
import json
import asyncio
from pathlib import Path
from aiohttp import web

from .storage import get_storage
from .learning_ai import get_ai
from .hashcat import get_hashcat, HashType
from .loop_cracker import get_cracker


class DualServer:
    """Web server with API endpoints for the cracker"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8888, data_dir: str = None):
        self.host = host
        self.port = port
        self.data_dir = data_dir

        self.storage = get_storage(data_dir)
        self.ai = get_ai(data_dir)
        self.hashcat = get_hashcat()
        self.cracker = get_cracker(data_dir)

        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""
        self.app.router.add_get("/", self.serve_index)
        self.app.router.add_get("/app.js", self.serve_js)
        self.app.router.add_get("/styles.css", self.serve_css)

        # API endpoints
        self.app.router.add_get("/api/status", self.api_status)
        self.app.router.add_get("/api/stats", self.api_stats)

        # Patterns
        self.app.router.add_get("/api/patterns", self.api_patterns)
        self.app.router.add_post("/api/patterns/add", self.api_add_pattern)

        # Learning AI
        self.app.router.add_post("/api/learn", self.api_learn)
        self.app.router.add_post("/api/generate", self.api_generate)
        self.app.router.add_get("/api/ai/stats", self.api_ai_stats)

        # Hashcat
        self.app.router.add_get("/api/hashcat/status", self.api_hashcat_status)
        self.app.router.add_post("/api/hashcat/crack", self.api_hashcat_crack)
        self.app.router.add_post("/api/hashcat/stop", self.api_hashcat_stop)

        # Loop Cracker
        self.app.router.add_get("/api/loop/status", self.api_loop_status)
        self.app.router.add_post("/api/loop/start", self.api_loop_start)
        self.app.router.add_post("/api/loop/stop", self.api_loop_stop)

        # Cracked passwords
        self.app.router.add_get("/api/cracked", self.api_cracked)

        # Hash generation
        self.app.router.add_post("/api/hash", self.api_hash)

        # Training mode - exhaustive pattern generation
        self.app.router.add_post("/api/train", self.api_train)

        # Target tracking
        self.app.router.add_get("/api/targets", self.api_targets)
        self.app.router.add_post("/api/targets", self.api_add_target)
        self.app.router.add_get("/api/targets/{target_id}/history", self.api_target_history)
        self.app.router.add_get("/api/targets/{target_id}/predict", self.api_target_predict)
        self.app.router.add_post("/api/targets/{target_id}/track", self.api_target_track)

        # Pattern categories
        self.app.router.add_get("/api/categories", self.api_categories)
        self.app.router.add_post("/api/categories", self.api_set_categories)
        self.app.router.add_get("/api/categories/{name}/masks", self.api_category_masks)

        # Config
        self.app.router.add_get("/api/config", self.api_config)
        self.app.router.add_post("/api/config", self.api_set_config)

    def _get_static_path(self, filename: str) -> Path:
        """Get path to static file"""
        return Path(__file__).parent / "static" / filename

    async def serve_index(self, request):
        """Serve index.html"""
        path = self._get_static_path("index.html")
        if path.exists():
            return web.FileResponse(path)
        return web.Response(text="<h1>NanoPy Dual</h1><p>Static files not found</p>",
                          content_type="text/html")

    async def serve_js(self, request):
        """Serve app.js"""
        path = self._get_static_path("app.js")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return web.Response(text=content, content_type="application/javascript")
        return web.Response(text="// app.js not found", content_type="application/javascript")

    async def serve_css(self, request):
        """Serve styles.css"""
        path = self._get_static_path("styles.css")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return web.Response(text=content, content_type="text/css")
        return web.Response(text="/* styles.css not found */", content_type="text/css")

    # ========== API Endpoints ==========

    async def api_status(self, request):
        """General status"""
        return web.json_response({
            "ok": True,
            "version": "1.0.0",
            "hashcat_available": self.hashcat.is_available(),
            "loop_running": self.cracker.is_running()
        })

    async def api_stats(self, request):
        """Get all statistics"""
        storage_stats = self.storage.get_stats()
        ai_stats = self.ai.get_stats()
        loop_stats = self.cracker.get_stats()

        return web.json_response({
            "storage": storage_stats,
            "ai": ai_stats,
            "loop": loop_stats
        })

    async def api_patterns(self, request):
        """Get learned patterns"""
        limit = int(request.query.get("limit", 100))
        min_count = int(request.query.get("min_count", 1))
        patterns = self.storage.get_patterns(limit=limit, min_count=min_count)
        return web.json_response({"patterns": patterns, "total": len(patterns)})

    async def api_add_pattern(self, request):
        """Add a pattern manually"""
        data = await request.json()
        pattern = data.get("pattern", "")
        if not pattern:
            return web.json_response({"error": "pattern required"}, status=400)

        mask = self.ai.pattern_to_mask(pattern)
        pid = self.storage.add_pattern(pattern, mask)
        return web.json_response({"ok": True, "id": pid, "mask": mask})

    async def api_learn(self, request):
        """Learn from password(s)"""
        data = await request.json()
        passwords = data.get("passwords", [])
        password = data.get("password")

        if password:
            passwords.append(password)

        if not passwords:
            return web.json_response({"error": "password(s) required"}, status=400)

        self.ai.learn_batch(passwords)
        return web.json_response({
            "ok": True,
            "learned": len(passwords),
            "total_patterns": len(self.ai.patterns)
        })

    async def api_generate(self, request):
        """Generate passwords"""
        data = await request.json()
        count = data.get("count", 10)
        length = data.get("length", 8)
        method = data.get("method", "auto")

        passwords = self.ai.generate_batch(count, length, method)
        return web.json_response({"passwords": passwords})

    async def api_ai_stats(self, request):
        """Get AI learning stats"""
        return web.json_response(self.ai.get_stats())

    async def api_hashcat_status(self, request):
        """Get hashcat status"""
        return web.json_response(self.hashcat.get_status())

    async def api_hashcat_crack(self, request):
        """Crack hash with hashcat (single attack)"""
        data = await request.json()
        target_hash = data.get("hash", "")
        hash_type = data.get("hash_type", "sha256")
        mask = data.get("mask")
        length = data.get("length", 8)
        timeout = data.get("timeout", 120)

        if not target_hash:
            return web.json_response({"error": "hash required"}, status=400)

        # Get hash type
        hash_types = {
            "md5": HashType.MD5,
            "sha1": HashType.SHA1,
            "sha256": HashType.SHA256,
            "sha512": HashType.SHA512,
        }
        ht = hash_types.get(hash_type.lower(), HashType.SHA256)

        # Get masks
        if mask:
            masks = [mask]
        else:
            masks = self.storage.get_masks_for_length(length, limit=100)
            if not masks:
                masks = self.ai.get_top_masks(length, limit=50)
            if not masks:
                masks = ["?l" * length, "?u" * length, "?d" * length]

        result = self.hashcat.crack_hcmask(target_hash, masks, ht, timeout)

        if result:
            # Save cracked
            pattern = self.ai.get_pattern(result)
            self.storage.add_cracked(target_hash, result, hash_type, pattern, "hashcat")
            self.ai.learn(result)

        return web.json_response({
            "cracked": result is not None,
            "password": result,
            "masks_tried": len(masks)
        })

    async def api_hashcat_stop(self, request):
        """Stop hashcat"""
        self.hashcat.stop()
        return web.json_response({"ok": True})

    async def api_loop_status(self, request):
        """Get loop cracker status"""
        return web.json_response(self.cracker.get_stats())

    async def api_loop_start(self, request):
        """Start the infinite loop cracker"""
        data = await request.json()
        target_hash = data.get("hash", "")
        hash_type = data.get("hash_type", "sha256")
        min_length = data.get("min_length", 6)
        max_length = data.get("max_length", 10)
        smart_mode = data.get("smart_mode", True)  # Default ON
        fresh_start = data.get("fresh_start", True)  # Default: reset progress

        # Support legacy 'length' parameter
        if "length" in data and "min_length" not in data:
            min_length = data["length"]
            max_length = data["length"]

        if not target_hash:
            return web.json_response({"error": "hash required"}, status=400)

        # Check if already cracked
        existing = self.storage.get_cracked(target_hash)
        if existing:
            return web.json_response({
                "already_cracked": True,
                "password": existing
            })

        try:
            self.cracker.start(target_hash, hash_type, min_length, max_length, smart_mode, fresh_start)
            return web.json_response({
                "ok": True,
                "started": True,
                "min_length": min_length,
                "max_length": max_length,
                "smart_mode": smart_mode,
                "fresh_start": fresh_start
            })
        except RuntimeError as e:
            return web.json_response({"error": str(e)}, status=400)

    async def api_loop_stop(self, request):
        """Stop the loop cracker"""
        self.cracker.stop()
        return web.json_response({"ok": True, "stopped": True})

    async def api_cracked(self, request):
        """Get list of cracked passwords"""
        limit = int(request.query.get("limit", 100))
        cracked = self.storage.get_cracked_list(limit=limit)
        return web.json_response({"cracked": cracked, "total": len(cracked)})

    async def api_hash(self, request):
        """Generate hash from password"""
        data = await request.json()
        password = data.get("password", "")
        hash_type = data.get("hash_type", "sha256")

        if not password:
            return web.json_response({"error": "password required"}, status=400)

        hash_types = {
            "md5": HashType.MD5,
            "sha1": HashType.SHA1,
            "sha256": HashType.SHA256,
            "sha512": HashType.SHA512,
        }
        ht = hash_types.get(hash_type.lower(), HashType.SHA256)

        hash_value = self.hashcat.hash_string(password, ht)
        return web.json_response({
            "password": password,
            "hash_type": hash_type,
            "hash": hash_value
        })

    async def api_train(self, request):
        """Training mode - generate ALL patterns exhaustively for a length range"""
        data = await request.json()
        min_length = data.get("min_length", 4)
        max_length = data.get("max_length", 8)

        total_patterns = 0
        results = {}

        for length in range(min_length, max_length + 1):
            patterns = self.ai.generate_exhaustive_patterns(length)
            results[length] = len(patterns)
            total_patterns += len(patterns)

        return web.json_response({
            "ok": True,
            "total_patterns": total_patterns,
            "by_length": results,
            "total_in_db": len(self.ai.patterns)
        })

    # ========== TARGET TRACKING ==========

    async def api_targets(self, request):
        """Get all tracked targets"""
        limit = int(request.query.get("limit", 100))
        targets = self.storage.get_all_targets(limit)
        return web.json_response({"targets": targets, "total": len(targets)})

    async def api_add_target(self, request):
        """Add a new target to track"""
        data = await request.json()
        target_id = data.get("target_id", "")
        name = data.get("name", "")

        if not target_id:
            return web.json_response({"error": "target_id required"}, status=400)

        self.storage.add_target(target_id, name)
        return web.json_response({"ok": True, "target_id": target_id})

    async def api_target_history(self, request):
        """Get pattern evolution history for a target"""
        target_id = request.match_info["target_id"]
        history = self.storage.get_target_history(target_id)
        return web.json_response({
            "target_id": target_id,
            "history": history,
            "count": len(history)
        })

    async def api_target_predict(self, request):
        """Predict next likely patterns for a target"""
        target_id = request.match_info["target_id"]
        prediction = self.storage.predict_next_pattern(target_id)

        # Also get suggested masks
        length = request.query.get("length")
        length = int(length) if length else None
        masks = self.storage.get_target_suggested_masks(target_id, length)

        prediction["suggested_masks"] = masks
        return web.json_response(prediction)

    async def api_target_track(self, request):
        """Track a cracked password for a target"""
        target_id = request.match_info["target_id"]
        data = await request.json()

        hash_val = data.get("hash", "")
        password = data.get("password", "")

        if not hash_val or not password:
            return web.json_response({"error": "hash and password required"}, status=400)

        # Get pattern from AI
        pattern = self.ai.get_pattern(password)

        # Track it
        self.storage.track_cracked_pattern(target_id, hash_val, password, pattern)

        return web.json_response({
            "ok": True,
            "target_id": target_id,
            "pattern": pattern,
            "prediction": self.storage.predict_next_pattern(target_id)
        })

    # ========== PATTERN CATEGORIES ==========

    async def api_categories(self, request):
        """Get all pattern categories with their frequencies"""
        categories = self.cracker.get_category_info()

        # Add mask count for a sample length
        sample_length = int(request.query.get("length", 8))
        for cat in categories:
            masks = self.cracker._get_category_masks(cat["name"], sample_length)
            cat["mask_count"] = len(masks)
            cat["sample_masks"] = masks[:3]  # First 3 as examples

        return web.json_response({
            "categories": categories,
            "sample_length": sample_length,
            "total_categories": len(categories)
        })

    async def api_category_masks(self, request):
        """Get all masks for a specific category and length"""
        category_name = request.match_info["name"]
        length = int(request.query.get("length", 8))

        # Validate category
        valid_categories = [c["name"] for c in self.cracker.PATTERN_CATEGORIES]
        if category_name not in valid_categories:
            return web.json_response({
                "error": f"Invalid category. Valid: {valid_categories}"
            }, status=400)

        masks = self.cracker._get_category_masks(category_name, length)

        # Get category info
        category_info = next(
            (c for c in self.cracker.PATTERN_CATEGORIES if c["name"] == category_name),
            None
        )

        return web.json_response({
            "category": category_name,
            "description": category_info["description"] if category_info else "",
            "frequency": category_info["frequency"] if category_info else 0,
            "length": length,
            "masks": masks,
            "count": len(masks)
        })

    # ========== CONFIG ==========

    async def api_config(self, request):
        """Get current config"""
        return web.json_response({
            "batch_size": self.cracker.batch_size,
            "attack_timeout": self.cracker.attack_timeout,
            "max_masks_per_attack": self.cracker.max_masks_per_attack,
            "max_keyspace": self.cracker.max_keyspace,
            "sequential_mode": self.cracker.sequential_mode,
            "smart_mode": self.cracker.smart_mode
        })

    async def api_set_config(self, request):
        """Update config"""
        data = await request.json()

        if "batch_size" in data:
            self.cracker.batch_size = int(data["batch_size"])
        if "attack_timeout" in data:
            self.cracker.attack_timeout = int(data["attack_timeout"])
        if "max_masks_per_attack" in data:
            self.cracker.max_masks_per_attack = int(data["max_masks_per_attack"])
        if "max_keyspace" in data:
            self.cracker.max_keyspace = int(data["max_keyspace"])
        if "sequential_mode" in data:
            self.cracker.sequential_mode = bool(data["sequential_mode"])
        if "smart_mode" in data:
            self.cracker.set_smart_mode(bool(data["smart_mode"]))

        return web.json_response({
            "ok": True,
            "batch_size": self.cracker.batch_size,
            "attack_timeout": self.cracker.attack_timeout,
            "max_masks_per_attack": self.cracker.max_masks_per_attack,
            "max_keyspace": self.cracker.max_keyspace,
            "sequential_mode": self.cracker.sequential_mode,
            "smart_mode": self.cracker.smart_mode
        })

    # ========== CATEGORIES ==========

    async def api_categories(self, request):
        """Get all categories with enabled status"""
        categories = self.cracker.get_category_info()
        return web.json_response({
            "categories": categories,
            "enabled": self.cracker.get_enabled_categories()
        })

    async def api_set_categories(self, request):
        """Set which categories are enabled"""
        data = await request.json()
        enabled = data.get("enabled", [])
        self.cracker.set_enabled_categories(enabled)
        return web.json_response({
            "ok": True,
            "enabled": self.cracker.get_enabled_categories()
        })

    def run(self):
        """Run the server (blocking)"""
        print(f"Starting NanoPy Dual server on http://{self.host}:{self.port}")
        web.run_app(self.app, host=self.host, port=self.port, print=None)

    async def start_async(self):
        """Start server asynchronously"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"Server running on http://{self.host}:{self.port}")
        return runner


def run_server(host: str = "0.0.0.0", port: int = 8888, data_dir: str = None):
    """Run the server"""
    server = DualServer(host, port, data_dir)
    server.run()
