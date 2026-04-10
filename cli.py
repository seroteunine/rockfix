"""Interactive CLI menu for user input."""

import os


def get_directory() -> str:
    """Prompt for root directory with default.
    
    Returns:
        str: The selected directory path
    """
    default_dir = "/Volumes/IPOD/Music"
    print("\n" + "─" * 50)
    print("📁 MUSIC LIBRARY LOCATION")
    print("─" * 50)
    print(f"Enter the folder containing your music files")
    print(f"(Default: {default_dir})")
    print("Just press ENTER to use the default")
    print(f"\nFolder path [or press ENTER]: ", end="", flush=True)
    user_input = input().strip()
    
    if not user_input:
        return default_dir
    
    if os.path.isdir(user_input):
        return user_input
    else:
        print(f"Error: Directory '{user_input}' not found. Using default.")
        return default_dir


def get_conversion_options() -> dict:
    """Prompt for conversion options with default.
    
    Returns:
        dict: Dictionary with 'music' and 'art' boolean keys
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
    print("  3️⃣  Both (RECOMMENDED) ← if you're unsure, pick this!")
    print()
    print("Choice [or press ENTER for option 3]: ", end="", flush=True)
    user_input = input().strip()
    
    options = {
        "1": {"music": True, "art": False},
        "2": {"music": False, "art": True},
        "3": {"music": True, "art": True},
    }
    
    if not user_input:
        return options["3"]
    
    if user_input in options:
        return options[user_input]
    else:
        print("Invalid choice. Using default (both).")
        return options["3"]


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
        conversions: Dictionary with conversion options
    """
    conversion_str = ""
    if conversions["music"] and conversions["art"]:
        conversion_str = "Music files & Cover art"
    elif conversions["music"]:
        conversion_str = "Music files"
    else:
        conversion_str = "Cover art"
    
    print("\n" + "─" * 50)
    print("✓ READY TO CONVERT")
    print("─" * 50)
    print(f"Folder:     {root_dir}")
    print(f"Converting: {conversion_str}")
    print("─" * 50)
    print("Processing (this may take a while)...\n")
