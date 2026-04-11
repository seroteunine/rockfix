# rockfix

Fixes the common Rockbox incompatibilities that cause missing album art, blank tags, and unplayable tracks.

## What it fixes

- **FLAC > 48 kHz** — downsamples to 48 kHz (Rockbox's limit)
- **MP3 ID3v2.4 tags** — converts to ID3v2.3, which Rockbox actually parses correctly
- **Missing ALBUMARTIST** — sets it from the majority artist per album; compilations get "Various Artists"
- **Embedded FLAC art** — extracts it to `cover.jpg` (Rockbox ignores embedded FLAC art)
- **PNG cover art** — converts to JPEG (Rockbox doesn't support PNG)
- **Oversized cover art** — resizes anything above 200×200
- **Progressive JPEG art** — re-encodes as baseline JPEG (progressive breaks Rockbox)
- **Oversized embedded MP3 art** — resizes the embedded image

All changes are staged in a temp directory and only written back if the full run succeeds. Ctrl-C leaves your files untouched.

Supported formats: FLAC and MP3.

---

## Usage

### Docker (no setup required)

```bash
docker run --rm -it -v /path/to/music:/music seroteunin/rockfix:latest
```

`/path/to/music` can be your mounted device (e.g. `/Volumes/PLAYER`) or any local folder.

### Local

Requires Python 3.11+ and [ffmpeg](https://ffmpeg.org/download.html).

```bash
pip install -r requirements.txt
python3 -m rockfix
```

Processes `/music` by default.

---

After the run, macOS may say the disk is still in use — this happens because the Docker daemon holds the volume mount open briefly after the container exits. Force-unmount it with:

```bash
diskutil unmount force /Volumes/<device>
```

---

## Contributing

The code is split into four files — `audio.py` (sample rate), `tags.py` (ID3, ALBUMARTIST), `artwork.py` (cover art), `main.py` (orchestration). PRs welcome.
