"""Cover art processing — resizes artwork images to fit Rockbox constraints."""

import io
import os
from PIL import Image
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC


KNOWN_FILENAMES = {
    'cover.jpg', 'cover.jpeg', 'cover.png',
    'folder.jpg', 'folder.jpeg', 'folder.png',
    'albumart.jpg', 'albumart.jpeg', 'albumart.png',
    'front.jpg', 'front.jpeg', 'front.png',
    'artwork.jpg', 'artwork.jpeg', 'artwork.png',
    'art.jpg', 'art.jpeg', 'art.png',
    'album.jpg', 'album.jpeg', 'album.png',
    'back.jpg', 'back.jpeg', 'back.png',
    'disc.jpg', 'disc.jpeg', 'disc.png',
    'thumb.jpg', 'thumb.jpeg', 'thumb.png',
}

MAX_SIZE = 300


def is_artwork(filename: str) -> bool:
    return filename.lower() in KNOWN_FILENAMES


def process(file_path: str):
    """Resize an artwork image file if it exceeds MAX_SIZE."""
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


def _resize_bytes(data: bytes) -> bytes | None:
    """Resize image bytes to fit MAX_SIZE. Returns resized bytes or None if already fits."""
    img = Image.open(io.BytesIO(data))
    w, h = img.size
    if w <= MAX_SIZE and h <= MAX_SIZE:
        return None
    img = img.convert("RGB")
    img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def process_embedded_flac(file_path: str):
    """Resize embedded artwork in a FLAC file."""
    try:
        f = FLAC(file_path)
        if not f.pictures:
            return
        changed = False
        pictures = []
        for pic in f.pictures:
            resized = _resize_bytes(pic.data)
            if resized:
                print(f"  Resizing embedded art in {os.path.basename(file_path)}...")
                pic.data = resized
                pic.mime = "image/jpeg"
                changed = True
            pictures.append(pic)
        if changed:
            f.clear_pictures()
            for pic in pictures:
                f.add_picture(pic)
            f.save()
    except Exception as e:
        print(f"  Error processing embedded art in {os.path.basename(file_path)}: {e}")


def process_embedded_mp3(file_path: str):
    """Resize embedded artwork in an MP3 file."""
    try:
        f = MP3(file_path, ID3=ID3)
        if not f.tags:
            return
        changed = False
        for apic in f.tags.getall('APIC'):
            resized = _resize_bytes(apic.data)
            if resized:
                print(f"  Resizing embedded art in {os.path.basename(file_path)}...")
                apic.data = resized
                apic.mime = "image/jpeg"
                changed = True
        if changed:
            f.tags.save(file_path)
    except Exception as e:
        print(f"  Error processing embedded art in {os.path.basename(file_path)}: {e}")
