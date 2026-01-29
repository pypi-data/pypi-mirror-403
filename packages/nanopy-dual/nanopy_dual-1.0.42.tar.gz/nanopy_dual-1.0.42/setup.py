#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="nanopy-dual",
    version="1.0.42",
    author="NanoPy Team",
    author_email="dev@nanopy.chain",
    description="Hashcat GPU Cracker with Learning AI Loop",
    long_description="""# NanoPy Dual

Hashcat GPU cracker with infinite learning loop:
- **LEARN**: Generate random passwords, learn patterns
- **ATTACK**: Use all patterns as hashcat masks, GPU crack
- **REPEAT**: Loop until cracked

## Install

```bash
pip install nanopy-dual
```

## CLI Usage

```bash
# Start web server
nanopy-dual serve --port 8888

# Crack a hash (infinite loop mode)
nanopy-dual crack <hash> --type sha256 --length 8

# Learn patterns from passwords
nanopy-dual learn password1 password2 password3
nanopy-dual learn --file wordlist.txt

# Generate passwords with AI
nanopy-dual generate --count 10 --length 8 --method auto

# List learned patterns
nanopy-dual patterns --limit 50

# Show cracked passwords
nanopy-dual cracked

# Check hashcat
nanopy-dual hashcat check

# Generate hash from password
nanopy-dual hashcat hash "test" --type sha256
```

## Web UI

Open http://localhost:8888 after `nanopy-dual serve`:
- **Loop Cracker**: Start/stop infinite crack loop
- **Patterns**: View all learned patterns
- **Cracked**: History of cracked passwords
- **Learn AI**: Train the AI with passwords
- **Stats**: Storage and hashcat info

## How the Loop Works

1. **LEARN PHASE**
   - Generate 500 random passwords using various methods
   - Extract patterns (LLDUULLD, UUUUUU, etc.)
   - Learn bigrams/trigrams for Markov chains
   - Store in LevelDB + SQLite

2. **ATTACK PHASE**
   - Get all masks for target length
   - Write to .hcmask file
   - Run hashcat with ALL masks at once
   - GPU tests millions of combos per second

3. **REPEAT**
   - Not found? Go back to LEARN
   - More patterns = smarter attacks
   - The longer it runs, the smarter it gets!

## Pattern to Mask

| Pattern | Hashcat Mask |
|---------|--------------|
| LLLLLL | ?l?l?l?l?l?l |
| UUUUUU | ?u?u?u?u?u?u |
| LLDDDD | ?l?l?d?d?d?d |
| UlllllD | ?u?l?l?l?l?l?d |

## Features

- Dual storage: LevelDB (fast) + SQLite (queryable)
- Learning AI with multiple generation methods
- Pattern extraction and mask conversion
- Hashcat GPU integration
- Infinite loop until cracked
- Web UI for monitoring
- CLI for scripting

## Requirements

- Python 3.8+
- Hashcat (for GPU cracking)
- plyvel (for LevelDB)
""",
    long_description_content_type="text/markdown",
    url="https://github.com/Complexity-ML/hashcat-dual",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "nanopy_dual": ["static/*"],
    },
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "click>=8.0.0",
        "rich>=12.0.0",
        "plyvel>=1.5.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "nanopy-dual=nanopy_dual.main:cli",
            "nanopy-dual-gen=nanopy_dual.pattern_generator:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="hashcat gpu cracking password learning ai leveldb",
)
