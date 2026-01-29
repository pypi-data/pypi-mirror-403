#!/usr/bin/env python3
"""
QViewer - A fast PyQt5-based image viewer with navigation
"""
import sys
import argparse
import clipboard

def main():
    """Main entry point for the qviewer application."""
    parser = argparse.ArgumentParser(
        description='QViewer - Fast image viewer with navigation',
        epilog='Examples:\n'
               '  qviewer image.jpg                    # View single image\n'
               '  qviewer img1.jpg img2.png img3.gif   # View multiple images\n'
               '  qviewer /path/to/images/             # View all images in directory\n'
               '  qviewer -d 2 /path/to/images/        # Scan directory with max depth 2\n'
               '  qviewer c                            # Load from clipboard\n'
               '\n'
               'Navigation:\n'
               '  Arrow Left/Up     - Previous image\n'
               '  Arrow Right/Down  - Next image\n'
               '  Space             - Next image\n'
               '  Q or Escape       - Quit',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'paths',
        nargs='*',
        help='Image file(s), URL(s), or directory path(s). Use "c" to load from clipboard'
    )
    
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=-1,
        metavar='N',
        help='Maximum directory recursion depth (default: infinite, 0: current dir only)'
    )
    
    args = parser.parse_args()
    
    # Handle no arguments
    if not args.paths:
        parser.print_help()
        sys.exit(1)
    
    # Import here to avoid issues with Cython compilation
    from qviewer.viewer import show, collect_all_images
    
    paths = args.paths
    
    # Handle clipboard shortcut
    if len(paths) == 1 and paths[0].lower() == 'c':
        clipboard_content = clipboard.paste()
        if not clipboard_content:
            print("Error: Clipboard is empty")
            sys.exit(1)
        paths = [clipboard_content]
    
    # Collect all images from the provided paths
    image_list = collect_all_images(paths, args.depth)
    
    if not image_list:
        print("Error: No images found in the specified path(s)")
        print(f"Paths searched: {paths}")
        if args.depth >= 0:
            print(f"Depth limit: {args.depth}")
        sys.exit(1)
    
    print(f"Found {len(image_list)} image(s)")
    
    # Show the viewer
    show(image_list)

if __name__ == "__main__":
    main()