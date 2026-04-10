"""Cover art processing utilities."""

import os
from PIL import Image


ARTWORK_FILENAMES = [
    'cover.jpg', 'cover.png',
    'folder.jpg', 'folder.png',
    'albumart.jpg', 'albumart.png'
]

MAX_ARTWORK_SIZE = 300


def is_artwork_file(filename: str) -> bool:
    """Check if file is a recognized artwork file.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        bool: True if file is artwork
    """
    return filename.lower() in ARTWORK_FILENAMES


def process_artwork(file_path: str) -> bool:
    """Process artwork file and resize if needed.
    
    Args:
        file_path: Path to the artwork file
        
    Returns:
        bool: True if processing was successful or not needed
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            
            if width > MAX_ARTWORK_SIZE or height > MAX_ARTWORK_SIZE:
                return _resize_artwork(file_path, img, width, height)
            
            return True
            
    except Exception as e:
        print(f"  Error processing {os.path.basename(file_path)}: {e}")
        return False


def _resize_artwork(file_path: str, img: Image.Image, width: int, height: int) -> bool:
    """Resize artwork to max size and save.
    
    Args:
        file_path: Path to save the resized artwork
        img: PIL Image object
        width: Original width
        height: Original height
        
    Returns:
        bool: True if resize was successful
    """
    try:
        print(f"  Resizing {os.path.basename(file_path)} from {width}x{height} to {MAX_ARTWORK_SIZE}x{MAX_ARTWORK_SIZE}...")
        img_rgb = img.convert("RGB")
        img_rgb.thumbnail((MAX_ARTWORK_SIZE, MAX_ARTWORK_SIZE), Image.LANCZOS)
        img_rgb.save(file_path, "JPEG", quality=85)
        return True
        
    except Exception as e:
        print(f"    Error resizing: {e}")
        return False
