"""Cover art processing — resizes artwork images to fit Rockbox constraints."""

import os
from PIL import Image


KNOWN_FILENAMES = {
    'cover.jpg', 'cover.png',
    'folder.jpg', 'folder.png',
    'albumart.jpg', 'albumart.png',
}

MAX_SIZE = 300


def is_artwork(filename: str) -> bool:
    return filename.lower() in KNOWN_FILENAMES


def process(file_path: str):
    try:
        with Image.open(file_path) as img:
            w, h = img.size
            if w <= MAX_SIZE and h <= MAX_SIZE:
                return
            print(f"  Resizing {os.path.basename(file_path)} ({w}x{h} → {MAX_SIZE}x{MAX_SIZE})...")
            out = img.convert("RGB")
            out.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
            out.save(file_path, "JPEG", quality=85)
    except Exception as e:
        print(f"  Error processing {os.path.basename(file_path)}: {e}")
