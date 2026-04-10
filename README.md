# RockBox compatibility tool

A simple tool to fix incompatibility issues on RockBox.

## Quick Start

### Using Docker (Recommended)

**Option 1: Use pre-built image from Docker Hub (easiest)**

```bash
docker run -it -v /path/to/music:/music seroteunin/rockfix:latest
```

This pulls and runs the latest version automatically—no building required!

**Option 2: Build locally**

```bash
docker build -t rockfix .
docker run -it -v /path/to/music:/music rockfix
```

### Local Installation

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Install ffmpeg:** (macOS: `brew install ffmpeg`, Linux: `apt-get install ffmpeg`, Windows: download from https://ffmpeg.org/download.html)
3. **Run:** `python3 -m rockfix`
4. **Answer the prompts** (or just press ENTER for defaults)
