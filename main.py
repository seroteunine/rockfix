"""RockBox Music Converter — prepares a music library for Rockbox devices."""

import os
import shutil
import signal
import sys
import tempfile

from . import audio
from . import artwork
from . import tags

DEFAULT_MUSIC_DIR = "/music"


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
        shutil.copy2(real_path, staged)
        self._staged.append(real_path)
        return staged

    def apply(self, changed: set[str]):
        """Copy only changed staged files back to the source.

        Files that were staged but no longer exist (e.g. PNG removed after PNG→JPEG
        conversion) are deleted from the real path.
        """
        for staged in changed:
            if os.path.exists(staged):
                real = self.real_path(staged)
                os.makedirs(os.path.dirname(real), exist_ok=True)
                shutil.copy2(staged, real)

        for real_path in self._staged:
            staged_path = self.tmp_path(real_path)
            if not os.path.exists(staged_path) and os.path.exists(real_path):
                os.remove(real_path)

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def _handle_interrupt(sig, frame):
    global _staging
    print("\n\nInterrupted — cleaning up temp files. No changes were made to your music.")
    if _staging:
        _staging.cleanup()
    sys.exit(0)


def _process(root_dir: str):
    global _staging
    _staging = _Staging(root_dir)
    signal.signal(signal.SIGINT, _handle_interrupt)
    signal.signal(signal.SIGTERM, _handle_interrupt)

    try:
        print(f"\nFolder:  {root_dir}")
        print(f"Staging: {_staging.tmp}")
        print("─" * 50)

        changed: set[str] = set()
        scanned = 0

        for root, _, files in os.walk(root_dir):
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

            if not (flacs or mp3s or any(artwork.is_artwork(f) for f in clean)):
                continue

            album_changed: set[str] = set()
            album_scanned = 0

            if flacs or mp3s:
                album_changed.update(tags.fix_album_artist(flacs + mp3s))

            for f in clean:
                staged = _staging.tmp_path(os.path.join(root, f))
                if f.lower().endswith('.flac'):
                    album_scanned += 1
                    if audio.process(staged):                album_changed.add(staged)
                    if artwork.process_embedded_flac(staged): album_changed.add(staged)
                elif f.lower().endswith('.mp3'):
                    album_scanned += 1
                    if tags.fix_mp3_id3_version(staged):     album_changed.add(staged)
                    if artwork.process_embedded_mp3(staged):  album_changed.add(staged)
                elif artwork.is_artwork(f):
                    album_scanned += 1
                    if artwork.process(staged):              album_changed.add(staged)

            n_album_changed = len(album_changed)
            status = f"{n_album_changed} modified" if n_album_changed else "OK"
            print(f"{root}  [{status}]")

            changed.update(album_changed)
            scanned += album_scanned

        n_changed = len(changed)
        n_ok = scanned - n_changed
        print("\n" + "─" * 50)
        print("Applying changes to device...")
        _staging.apply(changed)
        print(f"{n_changed} modified, {n_ok} already OK.")

    finally:
        _staging.cleanup()
        _staging = None


def main():
    _process(DEFAULT_MUSIC_DIR)
    print("\nDone. Your files are ready for your device.\n")


if __name__ == "__main__":
    main()
