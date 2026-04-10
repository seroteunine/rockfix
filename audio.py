"""Audio file conversion utilities."""

import os
import subprocess
from mutagen.flac import FLAC


def process_flac(file_path: str) -> bool:
    """Process a FLAC file and downsample if needed.
    
    Args:
        file_path: Path to the FLAC file
        
    Returns:
        bool: True if processing was successful or not needed
    """
    try:
        audio = FLAC(file_path)
        info = audio.info
        sample_rate = info.sample_rate
        
        # Convert to lower resolution if sample rate > 48000 Hz
        if sample_rate > 48000:
            print(f"  Converting {os.path.basename(file_path)} to 48000 Hz...")
            return _downsample_flac(file_path)
        
        return True
        
    except Exception as e:
        print(f"  Error reading {os.path.basename(file_path)}: {e}")
        return False


def _downsample_flac(file_path: str) -> bool:
    """Downsample FLAC file to 48kHz using ffmpeg.
    
    Args:
        file_path: Path to the FLAC file
        
    Returns:
        bool: True if conversion was successful
    """
    temp_path = file_path + ".temp.flac"
    try:
        subprocess.run([
            'ffmpeg', '-i', file_path, '-acodec', 'flac', '-ar', '48000', 
            '-y', temp_path
        ], capture_output=True, check=True)
        os.replace(temp_path, file_path)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"    Error: {e.stderr.decode()}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
