"""Cover art processing — converts and resizes artwork for Rockbox compatibility.

Rockbox constraints:
  - Supports JPEG and BMP only; PNG is not supported.
  - Does NOT read embedded art from FLAC (Vorbis comments) — external file required.
  - Does read embedded JPEG art from MP3 (ID3v2).
  - Progressive JPEGs are not supported; output must be baseline JPEG.
  - Recommended max size: 200x200 (theme-dependent, but 200x200 is the
    practical standard — most devices have screens smaller than this).
"""

import io
import os
from PIL import Image
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC


# Filenames Rockbox will actually find and display.
KNOWN_FILENAMES = {'cover.jpg', 'cover.jpeg', 'cover.png', 'folder.jpg', 'folder.jpeg', 'folder.png'}

MAX_SIZE = 200


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


def process(file_path: str) -> bool:
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
                    return True
                print(f"  Converting {os.path.basename(file_path)} (PNG → JPEG, Rockbox does not support PNG)...")
                out = img.convert("RGB")
                out.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
                out.save(jpg_path, "JPEG", quality=85, progressive=False)
                os.remove(file_path)
                return True

            elif w > MAX_SIZE or h > MAX_SIZE:
                print(f"  Resizing {os.path.basename(file_path)} ({w}x{h} → {MAX_SIZE}x{MAX_SIZE})...")
                out = img.convert("RGB")
                out.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
                out.save(file_path, "JPEG", quality=85, progressive=False)
                return True

            return False

    except Exception as e:
        print(f"  Error processing {os.path.basename(file_path)}: {e}")
        return False


def process_embedded_flac(real_path: str, staged_dir: str) -> str | None:
    """Extract embedded art from a FLAC file to cover.jpg in staged_dir.

    Rockbox does not read embedded FLAC (Vorbis comment) art — it only displays
    external image files. This extracts the embedded picture to cover.jpg so
    Rockbox can find it. Skips if any recognised cover file already exists in
    either the real album directory or the staging directory.

    Reads from the original FLAC path (no staging needed — the FLAC is not
    modified). Writes cover.jpg directly to staged_dir.
    Returns the staged cover.jpg path if created, else None.
    """
    real_dir = os.path.dirname(real_path)
    for n in KNOWN_FILENAMES:
        if (os.path.exists(os.path.join(real_dir, n)) or
                os.path.exists(os.path.join(staged_dir, n))):
            return None
    try:
        f = FLAC(real_path)
        if not f.pictures:
            return None
        os.makedirs(staged_dir, exist_ok=True)
        cover_path = os.path.join(staged_dir, "cover.jpg")
        jpg_data = _to_baseline_jpeg(f.pictures[0].data)
        with open(cover_path, "wb") as out:
            out.write(jpg_data)
        print(f"  Extracted embedded art → cover.jpg  ({os.path.basename(real_path)})")
        return cover_path
    except Exception as e:
        print(f"  Error extracting embedded art from {os.path.basename(real_path)}: {e}")
        return None


def process_embedded_mp3(real_path: str, stage_fn) -> str | None:
    """Resize embedded artwork in an MP3 file.

    Rockbox reads embedded JPEG art from ID3v2 tags. Oversized images are
    resized and re-encoded as baseline JPEG.

    Reads from the original path; stages and modifies only if oversized art
    is found. Returns the staged path if the file was modified, else None.
    """
    try:
        f = MP3(real_path, ID3=ID3)
        if not f.tags:
            return None
        apics = f.tags.getall("APIC")
        if not apics:
            return None
        # Check from original whether any resize is needed before staging.
        if not any(
            max(Image.open(io.BytesIO(apic.data)).size) > MAX_SIZE
            for apic in apics
        ):
            return None
        staged = stage_fn(real_path)
        f2 = MP3(staged, ID3=ID3)
        changed = False
        for apic in f2.tags.getall("APIC"):
            img = Image.open(io.BytesIO(apic.data))
            w, h = img.size
            if w <= MAX_SIZE and h <= MAX_SIZE:
                continue
            print(f"  Resizing embedded art in {os.path.basename(real_path)}...")
            apic.data = _to_baseline_jpeg(apic.data)
            apic.mime = "image/jpeg"
            changed = True
        if changed:
            f2.tags.save(staged)
        return staged if changed else None
    except Exception as e:
        print(f"  Error processing embedded art in {os.path.basename(real_path)}: {e}")
        return None
