"""Entry point for RockBox Music Converter."""

from ...rockfix import cli
from ...rockfix import processor


def main():
    """Main application entry point."""
    cli.print_header()
    
    root_dir = cli.get_directory()
    conversions = cli.get_conversion_options()
    
    cli.print_summary(root_dir, conversions)
    
    processor.process_directory(root_dir, conversions)
    
    print("=" * 50)
    print("✓ Conversion complete!")
    print("=" * 50)
    
    if not has_ffmpeg and conversions["music"]:
        print("\n⚠️  Note: Audio files were not downsampled because ffmpeg is not installed.")
        print("To enable audio conversion, install ffmpeg:")
        print("  macOS:  brew install ffmpeg")
        print("  Ubuntu: sudo apt-get install ffmpeg\n")
    else:
        print("\n✓ Your files are ready for your device! 🎉\n")


if __name__ == "__main__":
    main()
