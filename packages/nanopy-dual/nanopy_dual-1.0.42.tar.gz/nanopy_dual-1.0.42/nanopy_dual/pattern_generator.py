#!/usr/bin/env python3
"""
Pattern Generator - Generates patterns via API and feeds hashcat

Usage:
    python -m nanopy_dual.pattern_generator --min-len 5 --max-len 10 --count 1000
    python -m nanopy_dual.pattern_generator --length 6 --count 5000 --infinite
"""
import argparse
import requests
import time
import sys

API_BASE = "http://localhost:8888/api"


def api_get(endpoint):
    """GET request to API"""
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        return resp.json()
    except Exception as e:
        print(f"[ERROR] API GET {endpoint}: {e}")
        return None


def api_post(endpoint, data):
    """POST request to API"""
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=30)
        return resp.json()
    except Exception as e:
        print(f"[ERROR] API POST {endpoint}: {e}")
        return None


def generate_patterns(min_len: int, max_len: int, count: int, method: str = "auto"):
    """Generate passwords and learn patterns for each length"""
    total_generated = 0
    total_patterns = 0

    for length in range(min_len, max_len + 1):
        print(f"\n[*] Generating {count} passwords of length {length}...")

        # Generate passwords via API
        data = api_post("/generate", {
            "count": count,
            "length": length,
            "method": method
        })

        if not data or "passwords" not in data:
            print(f"[!] Failed to generate for length {length}")
            continue

        passwords = data["passwords"]
        print(f"    Generated {len(passwords)} passwords")

        # Learn from generated passwords
        learn_data = api_post("/learn", {"passwords": passwords})

        if learn_data and "learned" in learn_data:
            total_generated += learn_data["learned"]
            total_patterns = learn_data.get("total_patterns", 0)
            print(f"    Learned: {learn_data['learned']}, Total patterns: {total_patterns}")

    return total_generated, total_patterns


def show_stats():
    """Show current stats"""
    data = api_get("/stats")
    if data:
        print("\n" + "=" * 50)
        print("STATS")
        print("=" * 50)
        if "storage" in data:
            print(f"  Patterns in DB: {data['storage'].get('patterns', 0)}")
            print(f"  Cracked: {data['storage'].get('cracked', 0)}")
            print(f"  Total learned: {data['storage'].get('total_learned', 0)}")
        if "ai" in data:
            print(f"  Unique patterns: {data['ai'].get('unique_patterns', 0)}")
            print(f"  Generation: {data['ai'].get('generation', 0)}")
        print("=" * 50)


def show_top_patterns(limit: int = 20):
    """Show top patterns"""
    data = api_get(f"/patterns?limit={limit}")
    if data and "patterns" in data:
        print(f"\nTop {limit} patterns:")
        print("-" * 60)
        print(f"{'#':<4} {'Pattern':<15} {'Mask':<20} {'Count':<8} {'Len':<4}")
        print("-" * 60)
        for i, p in enumerate(data["patterns"], 1):
            print(f"{i:<4} {p['pattern']:<15} {p['mask']:<20} {p['count']:<8} {p['length']:<4}")


def infinite_loop(min_len: int, max_len: int, batch_size: int, delay: int):
    """Run infinite generation loop"""
    print("\n[*] Starting infinite pattern generation loop...")
    print(f"    Length range: {min_len}-{max_len}")
    print(f"    Batch size: {batch_size} per length")
    print(f"    Delay between batches: {delay}s")
    print("    Press Ctrl+C to stop\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n{'='*50}")
            print(f"ITERATION {iteration}")
            print(f"{'='*50}")

            total, patterns = generate_patterns(min_len, max_len, batch_size)
            print(f"\n[+] Iteration {iteration} complete: {total} generated, {patterns} total patterns")

            if delay > 0:
                print(f"[*] Waiting {delay}s...")
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\n[*] Stopped by user")
        show_stats()


def main():
    parser = argparse.ArgumentParser(description="Generate patterns for nanopy-dual")
    parser.add_argument("--min-len", type=int, default=6, help="Minimum password length (default: 6)")
    parser.add_argument("--max-len", type=int, default=10, help="Maximum password length (default: 10)")
    parser.add_argument("--length", type=int, help="Single length (overrides min/max)")
    parser.add_argument("--count", type=int, default=500, help="Passwords per length (default: 500)")
    parser.add_argument("--method", default="auto", choices=["auto", "random", "pattern", "weighted", "markov", "genetic"],
                       help="Generation method (default: auto)")
    parser.add_argument("--infinite", action="store_true", help="Run infinite loop")
    parser.add_argument("--delay", type=int, default=5, help="Delay between iterations in infinite mode (default: 5s)")
    parser.add_argument("--stats", action="store_true", help="Show stats only")
    parser.add_argument("--top", type=int, help="Show top N patterns")
    parser.add_argument("--api", default="http://localhost:8888/api", help="API base URL")

    args = parser.parse_args()

    global API_BASE
    API_BASE = args.api

    # Check API is running
    status = api_get("/status")
    if not status:
        print("[ERROR] Cannot connect to nanopy-dual API")
        print(f"        Make sure server is running: nanopy-dual serve")
        sys.exit(1)

    print(f"[+] Connected to nanopy-dual v{status.get('version', '?')}")

    if args.stats:
        show_stats()
        return

    if args.top:
        show_top_patterns(args.top)
        return

    # Set length range
    min_len = args.length if args.length else args.min_len
    max_len = args.length if args.length else args.max_len

    if args.infinite:
        infinite_loop(min_len, max_len, args.count, args.delay)
    else:
        print(f"\n[*] Generating patterns for lengths {min_len}-{max_len}")
        print(f"    Count per length: {args.count}")
        print(f"    Method: {args.method}")

        total, patterns = generate_patterns(min_len, max_len, args.count, args.method)

        print(f"\n[+] Done! Generated {total} passwords, {patterns} total patterns in DB")
        show_stats()
        show_top_patterns(10)


if __name__ == "__main__":
    main()
