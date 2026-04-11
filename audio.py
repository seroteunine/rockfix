"""FLAC audio conversion — downsamples files above 48kHz for Rockbox."""

import os
import subprocess
from mutagen.flac import FLAC


def process(real_path: str, stage_fn) -> str | None:
    """Downsample a FLAC file to 48 kHz if it exceeds the Rockbox limit.

    Reads sample rate from the original path. Stages and converts only if
    needed. Returns the staged path if the file was modified, else None.
    """
    try:
        f = FLAC(real_path)
        if f.info.sample_rate <= 48000:
            return None
        staged = stage_fn(real_path)
        print(f"  Converting {os.path.basename(real_path)} ({f.info.sample_rate} Hz → 48000 Hz)...")
        _downsample(staged)
        return staged
    except Exception as e:
        print(f"  Error reading {os.path.basename(real_path)}: {e}")
        return None


def _downsample(file_path: str):
    tmp = file_path + ".tmp.flac"
    try:
        subprocess.run(
            ['ffmpeg', '-i', file_path, '-acodec', 'flac', '-ar', '48000', '-y', tmp],
            capture_output=True, check=True
        )
        os.replace(tmp, file_path)
    except subprocess.CalledProcessError as e:
        print(f"  Error converting {os.path.basename(file_path)}: {e.stderr.decode()}")
        if os.path.exists(tmp):
            os.remove(tmp)
