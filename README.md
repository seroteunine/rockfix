# RockBox compatibility tool

A simple tool to prepare music for RockBox devices and fix incompatibility issues.

## Quick Start

### Using Docker

```bash
docker build -t rockfix .
docker run -it -v /path/to/music:/music rockfix
```

### Local Installation

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Install ffmpeg:** (macOS: `brew install ffmpeg`, Linux: `apt-get install ffmpeg`, Windows: download from https://ffmpeg.org/download.html)
3. **Run:** `python3 -m rockfix`
4. **Answer the prompts** (or just press ENTER for defaults)
