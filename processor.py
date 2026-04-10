"""Main processing logic for walking directory and converting files."""

import os

from ...rockfix import audio
from ...rockfix import artwork


SKIP_PATTERNS = ('._',)  # macOS resource fork files


def process_directory(root_dir: str, conversions: dict):
    """Walk directory tree and process files based on conversion options.
    
    Args:
        root_dir: Root directory to process
        conversions: Dictionary with 'music' and 'art' boolean keys
    """
    for root, _, files in os.walk(root_dir):
        print(f"\n{root}")
        
        for file in files:
            # Skip system files
            if any(file.startswith(pattern) for pattern in SKIP_PATTERNS):
                continue
            
            # Process audio files
            if conversions['music'] and file.lower().endswith('.flac'):
                file_path = os.path.join(root, file)
                audio.process_flac(file_path)
            
            # Process artwork files
            elif conversions['art'] and artwork.is_artwork_file(file):
                file_path = os.path.join(root, file)
                artwork.process_artwork(file_path)
