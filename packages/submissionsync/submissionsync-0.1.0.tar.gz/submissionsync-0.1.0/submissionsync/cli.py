import argparse
import sys
import time
from pathlib import Path, WindowsPath
from .core import create_symlink_structure


def main():
    parser = argparse.ArgumentParser(
        description='Create shortcuts to latest submitted assignment versions',
        prog='submissionsync'
    )
    parser.add_argument(
        'source',
        nargs='?',
        help='Source directory containing student work (default: ~/UTC Sheffield)'
    )
    parser.add_argument(
        'output',
        nargs='?',
        help='Output directory for shortcuts (default: P:/Documents/Student Work - Latest Submissions)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    parser.add_argument(
        '--show-tree',
        action='store_true',
        help='Display directory tree before processing'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force recreation of all shortcuts'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print verbose debug information'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )

    args = parser.parse_args()

    # Set defaults
    source_path = Path(args.source) if args.source else Path.home() / "UTC Sheffield"
    output_path = Path(args.output) if args.output else WindowsPath("P:\\Documents") / "Student Work - Latest Submissions"

    print("\n" + "=" * 50)
    print("Creating shortcuts structure...")
    print("=" * 50 + "\n")

    if args.verbose:
        print("Verbose mode enabled: printing debug information.\n")

    start_time = time.perf_counter()
    try:
        create_symlink_structure(
            source_path,
            output_path,
            debug=args.debug or args.verbose,
            show_tree=args.show_tree,
            force=args.force
        )
        elapsed = time.perf_counter() - start_time

        print(f"\nShortcuts structure created at: {output_path}")
        print("\nYou can now browse the organized structure at:")
        print(f"  {output_path}")
        print(f"\nCompleted in {elapsed:.2f} seconds.")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
