"""Cover art processing — converts and resizes artwork for Rockbox compatibility.

Rockbox constraints:
  - Supports JPEG and BMP only; PNG is not supported.
  - Does NOT read embedded art from FLAC (Vorbis comments) — external file required.
  - Does read embedded JPEG art from MP3 (ID3v2).
  - Progressive JPEGs are not supported; output must be baseline JPEG.
  - Recommended max size: 300x300 (theme-dependent, but safe default).
"""

import io
import os
from PIL import Image
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC


# Filenames Rockbox will actually find and display.
KNOWN_FILENAMES = {'cover.jpg', 'cover.jpeg', 'cover.png', 'folder.jpg', 'folder.jpeg', 'folder.png'}

MAX_SIZE = 300


def is_artwork(filename: str) -> bool:
    return filename.lower() in KNOWN_FILENAMES


def _to_baseline_jpeg(data: bytes) -> bytes:
    """Convert image bytes to a resized, baseline (non-progressive) JPEG.

    Baseline JPEG is required — Rockbox cannot decode progressive JPEGs.
    Always resizes to MAX_SIZE and converts to RGB (strips alpha).
    """
    img = Image.open(io.BytesIO(data))
    img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
    out = img.convert("RGB")
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=85, progressive=False)
    return buf.getvalue()


def process(file_path: str):
    """Resize/convert a standalone artwork file for Rockbox compatibility.

    PNG files are converted to JPEG — Rockbox does not support PNG.
    Oversized JPEGs are resized in place.
    Output is always baseline (non-progressive) JPEG.
    """
    try:
        with Image.open(file_path) as img:
            w, h = img.size
            fmt = img.format or "JPEG"

            if fmt == "PNG":
                jpg_path = os.path.splitext(file_path)[0] + ".jpg"
                if os.path.exists(jpg_path):
                    # A JPEG already exists for this cover — just remove the PNG.
                    os.remove(file_path)
                    print(f"  Removed {os.path.basename(file_path)} (cover.jpg already present)")
                    return
                print(f"  Converting {os.path.basename(file_path)} (PNG → JPEG, Rockbox does not support PNG)...")
                out = img.convert("RGB")
                out.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
                out.save(jpg_path, "JPEG", quality=85, progressive=False)
                os.remove(file_path)

            elif w > MAX_SIZE or h > MAX_SIZE:
                print(f"  Resizing {os.path.basename(file_path)} ({w}x{h} → {MAX_SIZE}x{MAX_SIZE})...")
                out = img.convert("RGB")
                out.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
                out.save(file_path, "JPEG", quality=85, progressive=False)

    except Exception as e:
        print(f"  Error processing {os.path.basename(file_path)}: {e}")


def process_embedded_flac(file_path: str):
    """Extract embedded art from a FLAC file to cover.jpg in the same directory.

    Rockbox does not read embedded FLAC (Vorbis comment) art — it only displays
    external image files. This extracts the embedded picture to cover.jpg so
    Rockbox can find it. Skips if any recognised cover file already exists.
    """
    directory = os.path.dirname(file_path)
    if any(os.path.exists(os.path.join(directory, n)) for n in KNOWN_FILENAMES):
        return
    try:
        f = FLAC(file_path)
        if not f.pictures:
            return
        cover_path = os.path.join(directory, "cover.jpg")
        jpg_data = _to_baseline_jpeg(f.pictures[0].data)
        with open(cover_path, "wb") as out:
            out.write(jpg_data)
        print(f"  Extracted embedded art → cover.jpg  ({os.path.basename(file_path)})")
    except Exception as e:
        print(f"  Error extracting embedded art from {os.path.basename(file_path)}: {e}")


def process_embedded_mp3(file_path: str):
    """Resize embedded artwork in an MP3 file.

    Rockbox reads embedded JPEG art from ID3v2 tags. Oversized images are
    resized and re-encoded as baseline JPEG.
    """
    try:
        f = MP3(file_path, ID3=ID3)
        if not f.tags:
            return
        changed = False
        for apic in f.tags.getall("APIC"):
            img = Image.open(io.BytesIO(apic.data))
            w, h = img.size
            if w <= MAX_SIZE and h <= MAX_SIZE:
                continue
            print(f"  Resizing embedded art in {os.path.basename(file_path)}...")
            apic.data = _to_baseline_jpeg(apic.data)
            apic.mime = "image/jpeg"
            changed = True
        if changed:
            f.tags.save(file_path)
    except Exception as e:
        print(f"  Error processing embedded art in {os.path.basename(file_path)}: {e}")
