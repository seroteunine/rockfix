"""Metadata tag fixes for Rockbox database compatibility."""

import os
import re
from collections import Counter
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE2


_FEAT = re.compile(
    r'\s*\((?:feat\.?|ft\.?|featuring)\b[^)]*\)'
    r'|\s*\[(?:feat\.?|ft\.?|featuring)\b[^\]]*\]'
    r'|\s*(?:feat\.?|ft\.?|featuring)\b.*$',
    re.IGNORECASE
)


def _split(artist: str) -> list[str]:
    if ';' in artist:
        return [a.strip() for a in artist.split(';') if a.strip()]
    main = _FEAT.sub('', artist).strip()
    return [main] if main else []


def _open(path: str):
    return FLAC(path) if path.lower().endswith('.flac') else MP3(path, ID3=ID3)


def _get_artist(f) -> str | None:
    if isinstance(f, FLAC):
        vals = f.get('albumartist') or f.get('artist') or []
        return vals[0] if vals else None
    frame = f.tags and (f.tags.get('TPE2') or f.tags.get('TPE1'))
    return str(frame) if frame else None


def _get_albumartist(f) -> str | None:
    if isinstance(f, FLAC):
        vals = f.get('albumartist') or []
        return vals[0] if vals else None
    frame = f.tags and f.tags.get('TPE2')
    return str(frame) if frame else None


def _set_albumartist(f, path: str, value: str):
    if isinstance(f, FLAC):
        f['albumartist'] = value
        f.save()
    else:
        if f.tags is None:
            f.add_tags()
        f.tags['TPE2'] = TPE2(encoding=3, text=value)
        f.tags.save(path)


def fix_mp3_id3_version(path: str) -> bool:
    """Convert MP3 ID3 tags to v2.3 for Rockbox compatibility.

    Rockbox has known parser bugs with certain ID3v2.4 features that cause
    tags to show as unknown in the database. ID3v2.3 is the safe target.
    """
    try:
        f = ID3(path)
        if f.version[1] == 3:
            return False
        f.update_to_v23()
        f.save(path, v2_version=3)
        print(f"  ID3v2.3  {os.path.basename(path)}")
        return True
    except Exception as e:
        print(f"  Error converting ID3 version for {os.path.basename(path)}: {e}")
        return False


VARIOUS_ARTISTS = "Various Artists"


def fix_album_artist(audio_files: list[str]) -> set[str]:
    """Set a consistent ALBUMARTIST on every track in an album directory.

    If a single artist appears on more than 50% of the tracks, that artist
    is used as ALBUMARTIST. Otherwise the directory is treated as a
    compilation and ALBUMARTIST is set to "Various Artists".
    Supports both FLAC (Vorbis comments) and MP3 (ID3) files.
    Returns the set of paths that were modified.
    """
    loaded = []
    tally = Counter()

    for path in audio_files:
        try:
            f = _open(path)
            artist = _get_artist(f)
            artists = _split(artist) if artist else []
            for a in artists:
                tally[a] += 1
            loaded.append((path, f))
        except Exception as e:
            print(f"  Error reading {os.path.basename(path)}: {e}")

    if not tally:
        return set()

    top_artist, top_count = tally.most_common(1)[0]
    if top_count / len(loaded) >= 0.5:
        album_artist = top_artist
    else:
        album_artist = VARIOUS_ARTISTS

    modified = set()
    for path, f in loaded:
        if _get_albumartist(f) != album_artist:
            print(f"  Tagging  {os.path.basename(path)}: ALBUMARTIST={album_artist!r}")
            _set_albumartist(f, path, album_artist)
            modified.add(path)
    return modified
