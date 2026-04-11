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


def _get_artist(f) -> str | None:
    if isinstance(f, FLAC):
        source = f.get('albumartist') or f.get('artist') or []
        return source[0] if source else None
    else:
        tags = f.tags
        if not tags:
            return None
        frame = tags.get('TPE2') or tags.get('TPE1')
        return str(frame) if frame else None


def _get_albumartist(f) -> str | None:
    if isinstance(f, FLAC):
        source = f.get('albumartist') or []
        return source[0] if source else None
    else:
        tags = f.tags
        if not tags:
            return None
        frame = tags.get('TPE2')
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


def fix_album_artist(audio_files: list[str]):
    """Set a consistent ALBUMARTIST on every track in an album directory.

    Finds the artist that appears across the most tracks and writes it to
    all tracks, so Rockbox groups the album under a single artist entry.
    Supports both FLAC (Vorbis comments) and MP3 (ID3) files.
    """
    loaded = []
    tally = Counter()

    for path in audio_files:
        try:
            f = FLAC(path) if path.lower().endswith('.flac') else MP3(path, ID3=ID3)
            artist = _get_artist(f)
            artists = _split(artist) if artist else []
            for a in artists:
                tally[a] += 1
            loaded.append((path, f))
        except Exception as e:
            print(f"  Error reading {os.path.basename(path)}: {e}")

    if not tally:
        return

    album_artist = tally.most_common(1)[0][0]

    for path, f in loaded:
        if _get_albumartist(f) != album_artist:
            print(f"  Tagging  {os.path.basename(path)}: ALBUMARTIST={album_artist!r}")
            _set_albumartist(f, path, album_artist)
