"""Audio file conversion utilities."""

import os
import re
import subprocess
from mutagen.flac import FLAC


# Matches "feat. X", "(feat. X)", "[feat. X]", "ft. X", "featuring X"
_FEAT_PATTERN = re.compile(
    r'\s*\((?:feat\.?|ft\.?|featuring)\b[^)]*\)'   # (feat. X)
    r'|\s*\[(?:feat\.?|ft\.?|featuring)\b[^\]]*\]'  # [feat. X]
    r'|\s*(?:feat\.?|ft\.?|featuring)\b.*$',         # feat. X bare
    re.IGNORECASE
)


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


def _split_artists(value: str) -> list[str]:
    """Split a tag value into individual artist names.

    Handles semicolon-separated values ("Chief Keef; Lil Reese") and
    feat. patterns ("Drake feat. Lil Wayne"), returning only the main artist
    as a single-element list for feat. patterns.
    """
    if ';' in value:
        return [a.strip() for a in value.split(';') if a.strip()]
    main = _FEAT_PATTERN.sub('', value).strip()
    return [main] if main else []


def fix_album_albumartists(flac_files: list[str]) -> bool:
    """Set a consistent ALBUMARTIST across all tracks in an album.

    Rockbox groups albums by ALBUMARTIST. If tracks in the same album have
    different ALBUMARTIST values (e.g. because featured artists are listed in
    different orders), the album appears split under multiple artist entries.

    This function finds the single artist that appears across the most tracks
    and writes it as ALBUMARTIST to every track that differs.

    Args:
        flac_files: List of FLAC file paths belonging to the same album

    Returns:
        bool: True if all files were processed successfully
    """
    from collections import Counter

    # Read all tracks and tally which artist names appear across how many tracks
    loaded = []
    artist_track_count = Counter()

    for path in flac_files:
        try:
            audio = FLAC(path)
            # Prefer ALBUMARTIST as source if set, fall back to ARTIST
            source = audio.get('albumartist') or audio.get('artist') or []
            artists = _split_artists(source[0]) if source else []
            for a in artists:
                artist_track_count[a] += 1
            loaded.append((path, audio, artists))
        except Exception as e:
            print(f"  Error reading {os.path.basename(path)}: {e}")
            return False

    if not artist_track_count:
        return True

    # The album artist is whoever appears across the most tracks
    album_artist = artist_track_count.most_common(1)[0][0]

    success = True
    for path, audio, _ in loaded:
        existing = audio.get('albumartist', [None])[0]
        if existing != album_artist:
            try:
                print(f"  Tagging  {os.path.basename(path)}: ALBUMARTIST={album_artist!r}")
                audio['albumartist'] = album_artist
                audio.save()
            except Exception as e:
                print(f"  Error saving {os.path.basename(path)}: {e}")
                success = False

    return success


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
