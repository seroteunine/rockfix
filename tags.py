"""Metadata tag fixes for Rockbox database compatibility."""

import os
import re
from collections import Counter
from mutagen.flac import FLAC


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


def fix_album_artist(flac_files: list[str]):
    """Set a consistent ALBUMARTIST on every track in an album directory.

    Finds the artist that appears across the most tracks and writes it to
    all tracks, so Rockbox groups the album under a single artist entry.
    """
    loaded = []
    tally = Counter()

    for path in flac_files:
        try:
            f = FLAC(path)
            source = f.get('albumartist') or f.get('artist') or []
            artists = _split(source[0]) if source else []
            for a in artists:
                tally[a] += 1
            loaded.append((path, f))
        except Exception as e:
            print(f"  Error reading {os.path.basename(path)}: {e}")

    if not tally:
        return

    album_artist = tally.most_common(1)[0][0]

    for path, f in loaded:
        if f.get('albumartist', [None])[0] != album_artist:
            print(f"  Tagging  {os.path.basename(path)}: ALBUMARTIST={album_artist!r}")
            f['albumartist'] = album_artist
            f.save()
