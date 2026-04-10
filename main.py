"""Entry point for RockBox Music Converter."""

from . import cli
from . import processor


def main():
    """Main application entry point."""
    cli.print_header()
    
    root_dir = "/music"
    conversions = cli.get_conversion_options()
    
    cli.print_summary(root_dir, conversions)
    
    processor.process_directory(root_dir, conversions)
    
    print("=" * 50)
    print("✓ Conversion complete!")
    print("=" * 50)
    print("\n✓ Your files are ready for your device! 🎉\n")


if __name__ == "__main__":
    main()
