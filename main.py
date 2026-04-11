"""RockBox Music Converter — prepares a music library for Rockbox devices."""

import os

from . import audio
from . import artwork
from . import tags


SKIP_PREFIXES = ('._',)


def _prompt_options() -> dict:
    print("\n" + "=" * 50)
    print("🎵 ROCKBOX MUSIC CONVERTER 🎵")
    print("=" * 50)
    print("Preparing your music for your device...\n")

    print("─" * 50)
    print("⚙️  WHAT TO CONVERT")
    print("─" * 50)
    print("  1  Convert music files only")
    print("       Makes FLAC files compatible (max 48kHz)")
    print("  2  Convert cover art only")
    print("       Optimizes album artwork (max 300x300)")
    print("  3  Fix featured artist tags only")
    print("       Sets ALBUMARTIST so albums don't split by featured artist")
    print("  4  All (RECOMMENDED)")
    print()
    print("Choice [Enter = 4]: ", end="", flush=True)
    choice = input().strip() or "4"

    options = {
        "1": {"music": True,  "art": False, "tags": False},
        "2": {"music": False, "art": True,  "tags": False},
        "3": {"music": False, "art": False, "tags": True},
        "4": {"music": True,  "art": True,  "tags": True},
    }

    if choice not in options:
        print("Invalid choice. Using default (all).")
        choice = "4"

    return options[choice]


def _process(root_dir: str, conversions: dict):
    parts = [k for k, v in [("music", conversions["music"]), ("art", conversions["art"]), ("tags", conversions["tags"])] if v]
    print(f"\nFolder:  {root_dir}")
    print(f"Tasks:   {', '.join(parts)}")
    print("─" * 50)

    for root, _, files in os.walk(root_dir):
        print(f"\n{root}")

        clean = [f for f in files if not any(f.startswith(p) for p in SKIP_PREFIXES)]
        flacs = [os.path.join(root, f) for f in clean if f.lower().endswith('.flac')]

        if conversions['tags'] and flacs:
            tags.fix_album_artist(flacs)

        for f in clean:
            path = os.path.join(root, f)
            if conversions['music'] and f.lower().endswith('.flac'):
                audio.process(path)
            elif conversions['art'] and artwork.is_artwork(f):
                artwork.process(path)


def main():
    conversions = _prompt_options()
    _process("/music", conversions)
    print("\n" + "=" * 50)
    print("Done. Your files are ready for your device.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
