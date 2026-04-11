"""RockBox Music Converter — prepares a music library for Rockbox devices."""

import os
import shutil
import signal
import sys
import tempfile

from . import audio
from . import artwork
from . import tags


SKIP_PREFIXES = ('._',)

_staging = None  # kept at module level so the signal handler can reach it


class _Staging:
    """Mirrors files into a temp directory so the source volume is never
    written to mid-run. Changes are copied back only after all processing
    completes. An interrupted run leaves the source completely untouched."""

    def __init__(self, source_root: str):
        self.source_root = source_root
        self.tmp = tempfile.mkdtemp(prefix="rockfix_")
        self._staged: list[str] = []  # real paths copied into staging

    def tmp_path(self, real_path: str) -> str:
        """Return the staging path for a real path (does not create directories)."""
        rel = os.path.relpath(real_path, self.source_root)
        return os.path.join(self.tmp, rel)

    def real_path(self, tmp_path: str) -> str:
        rel = os.path.relpath(tmp_path, self.tmp)
        return os.path.join(self.source_root, rel)

    def stage(self, real_path: str) -> str:
        """Copy a file into the staging area and return its staged path."""
        staged = self.tmp_path(real_path)
        os.makedirs(os.path.dirname(staged), exist_ok=True)
        shutil.copy2(real_path, staged)  # copy2 preserves mtime
        self._staged.append(real_path)
        return staged

    def apply(self) -> int:
        """Copy staged changes back to the source. Returns the number of files written.

        Uses mtime to detect changes: shutil.copy2 preserves the original mtime
        when staging, so any file a processing function touches will have a newer
        mtime than the real file. New files (e.g. extracted cover.jpg) are copied
        because they don't exist at the real path yet. Files deleted during
        processing (e.g. original PNG after PNG→JPEG conversion) are removed from
        the real path.
        """
        written = 0

        for root, _, files in os.walk(self.tmp):
            for f in files:
                staged = os.path.join(root, f)
                real = self.real_path(staged)
                if (not os.path.exists(real) or
                        os.path.getmtime(staged) > os.path.getmtime(real)):
                    shutil.copy2(staged, real)
                    written += 1

        for real_path in self._staged:
            staged_path = self.tmp_path(real_path)
            if not os.path.exists(staged_path) and os.path.exists(real_path):
                os.remove(real_path)

        return written

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def _handle_interrupt(sig, frame):
    global _staging
    print("\n\nInterrupted — cleaning up temp files. No changes were made to your music.")
    if _staging:
        _staging.cleanup()
    sys.exit(0)


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
    global _staging
    _staging = _Staging(root_dir)
    signal.signal(signal.SIGINT, _handle_interrupt)
    signal.signal(signal.SIGTERM, _handle_interrupt)

    try:
        parts = [k for k, v in [
            ("music", conversions["music"]),
            ("art",   conversions["art"]),
            ("tags",  conversions["tags"]),
        ] if v]
        print(f"\nFolder:  {root_dir}")
        print(f"Tasks:   {', '.join(parts)}")
        print(f"Staging: {_staging.tmp}")
        print("─" * 50)

        for root, _, files in os.walk(root_dir):
            print(f"\n{root}")

            clean = [f for f in files if not any(f.startswith(p) for p in SKIP_PREFIXES)]

            # Copy all audio files and existing cover art into the staging area.
            # Processing functions then operate on staged copies, never touching
            # the real volume. Existing covers are staged so that
            # process_embedded_flac correctly detects them in the staged directory.
            flacs = [_staging.stage(os.path.join(root, f))
                     for f in clean if f.lower().endswith('.flac')]
            mp3s  = [_staging.stage(os.path.join(root, f))
                     for f in clean if f.lower().endswith('.mp3')]
            for f in clean:
                if artwork.is_artwork(f):
                    _staging.stage(os.path.join(root, f))

            if conversions['tags'] and (flacs or mp3s):
                tags.fix_album_artist(flacs + mp3s)

            for f in clean:
                staged = _staging.tmp_path(os.path.join(root, f))
                if f.lower().endswith('.flac'):
                    if conversions['music']:
                        audio.process(staged)
                    if conversions['art']:
                        artwork.process_embedded_flac(staged)
                elif f.lower().endswith('.mp3'):
                    if conversions['tags']:
                        tags.fix_mp3_id3_version(staged)
                    if conversions['art']:
                        artwork.process_embedded_mp3(staged)
                elif conversions['art'] and artwork.is_artwork(f):
                    artwork.process(staged)

        print("\n" + "─" * 50)
        print("Applying changes to device...")
        written = _staging.apply()
        print(f"{written} file(s) updated.")

    finally:
        _staging.cleanup()
        _staging = None


def main():
    conversions = _prompt_options()
    _process("/music", conversions)
    print("\n" + "=" * 50)
    print("Done. Your files are ready for your device.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
