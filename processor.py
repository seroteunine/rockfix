"""Main processing logic for walking directory and converting files."""

import os

from . import audio
from . import artwork


SKIP_PATTERNS = ('._',)  # macOS resource fork files


def process_directory(root_dir: str, conversions: dict):
    """Walk directory tree and process files based on conversion options.
    
    Args:
        root_dir: Root directory to process
        conversions: Dictionary with 'music' and 'art' boolean keys
    """
    for root, _, files in os.walk(root_dir):
        print(f"\n{root}")

        clean_files = [f for f in files if not any(f.startswith(p) for p in SKIP_PATTERNS)]
        flac_files = [os.path.join(root, f) for f in clean_files if f.lower().endswith('.flac')]

        # Fix ALBUMARTIST for the whole album directory at once so every track
        # ends up with the same value, regardless of per-track artist ordering
        if conversions['tags'] and flac_files:
            audio.fix_album_albumartists(flac_files)

        for file in clean_files:
            # Downsample high-res FLAC files
            if conversions['music'] and file.lower().endswith('.flac'):
                audio.process_flac(os.path.join(root, file))

            # Process artwork files
            elif conversions['art'] and artwork.is_artwork_file(file):
                artwork.process_artwork(os.path.join(root, file))
