"""Interactive CLI menu for user input."""

import os


def get_conversion_options() -> dict:
    """Prompt for conversion options with default.

    Returns:
        dict: Dictionary with 'music', 'art', and 'tags' boolean keys
    """
    print("\n" + "─" * 50)
    print("⚙️  WHAT TO CONVERT")
    print("─" * 50)
    print("Choose what you want to prepare for your device:\n")
    print("  1️⃣  Convert music files only")
    print("      • Makes FLAC files compatible (max 48kHz)")
    print()
    print("  2️⃣  Convert cover art only")
    print("      • Optimizes album artwork (max 300x300)")
    print()
    print("  3️⃣  Fix featured artist tags only")
    print("      • Sets ALBUMARTIST so albums don't split by featured artist")
    print()
    print("  4️⃣  All (RECOMMENDED) ← if you're unsure, pick this!")
    print()
    print("Choice [or press ENTER for option 4]: ", end="", flush=True)
    user_input = input().strip()

    options = {
        "1": {"music": True,  "art": False, "tags": False},
        "2": {"music": False, "art": True,  "tags": False},
        "3": {"music": False, "art": False, "tags": True},
        "4": {"music": True,  "art": True,  "tags": True},
    }

    if not user_input:
        return options["4"]

    if user_input in options:
        return options[user_input]
    else:
        print("Invalid choice. Using default (all).")
        return options["4"]


def print_header():
    """Print application header."""
    print("\n" + "=" * 50)
    print("🎵 ROCKBOX MUSIC CONVERTER 🎵")
    print("=" * 50)
    print("Preparing your music for your device...\n")


def print_summary(root_dir: str, conversions: dict):
    """Print processing summary.

    Args:
        root_dir: The root directory being processed
        conversions: Dictionary with 'music', 'art', and 'tags' boolean keys
    """
    parts = []
    if conversions["music"]:
        parts.append("Music files")
    if conversions["art"]:
        parts.append("Cover art")
    if conversions["tags"]:
        parts.append("Featured artist tags")

    conversion_str = " & ".join(parts) if parts else "Nothing selected"

    print("\n" + "─" * 50)
    print("✓ READY TO CONVERT")
    print("─" * 50)
    print(f"Folder:     {root_dir}")
    print(f"Converting: {conversion_str}")
    print("─" * 50)
    print("Processing (this may take a while)...\n")
