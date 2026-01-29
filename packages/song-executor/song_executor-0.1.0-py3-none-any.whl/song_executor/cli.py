"""Command-line interface for song-executor."""

import argparse
import sys

from song_executor.executor import SongExecutor


def main():
    """Main entry point for the song-executor CLI."""
    parser = argparse.ArgumentParser(
        description="Execute song-schema JSON files in Ableton Live",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview structure without executing
  song-executor song.json --dry-run

  # Execute and record to arrangement view
  song-executor song.json --record

  # Execute without recording
  song-executor song.json

  # Play only a specific section
  song-executor song.json --section chorus
"""
    )

    parser.add_argument(
        "song_file",
        help="Path to the song.json file"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print structure and timing without executing"
    )

    parser.add_argument(
        "--record",
        action="store_true",
        help="Enable arrangement recording"
    )

    parser.add_argument(
        "--section",
        type=str,
        help="Execute only a specific section by name"
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Print song info and exit"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=11001,
        help="OSC receive port (default: 11001). Use a different port if MCP server is running."
    )

    args = parser.parse_args()

    try:
        executor = SongExecutor(args.song_file, receive_port=args.port)
        executor.load()

        if args.info:
            executor.print_structure()
            return 0

        if args.section:
            executor.execute_section(args.section)
        else:
            executor.execute(record=args.record, dry_run=args.dry_run)

        return 0

    except FileNotFoundError:
        print(f"Error: File not found: {args.song_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
