"""
Command-line interface for video2frames.
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .extractor import (
    extract_frames,
    get_video_info,
    check_ffmpeg,
    FFmpegNotFoundError,
    VideoNotFoundError,
    ExtractionError,
)


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="video2frames",
        description="Extract frames from video files using FFmpeg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract 1 frame per second as JPG
  video2frames video.mp4 -o frames/

  # Extract at 5 fps as PNG
  video2frames video.mp4 -o frames/ -f 5 --format png

  # Extract frames from 10s to 20s at 2 fps
  video2frames video.mp4 -o frames/ -f 2 --start 10 --end 20

  # Extract with custom prefix and quality
  video2frames video.mp4 -o frames/ --prefix screenshot --quality 95

  # Extract and resize to 720p height
  video2frames video.mp4 -o frames/ --scale -1:720

  # Show video information only
  video2frames video.mp4 --info
        """
    )

    parser.add_argument(
        "video",
        help="Path to input video file"
    )
    parser.add_argument(
        "-o", "--output",
        default="frames",
        help="Output directory (default: frames)"
    )
    parser.add_argument(
        "-f", "--fps",
        type=float,
        default=1.0,
        help="Frames per second to extract (default: 1)"
    )
    parser.add_argument(
        "--format",
        choices=["jpg", "png", "webp"],
        default="jpg",
        help="Output image format (default: jpg)"
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=90,
        help="Image quality 1-100 (default: 90)"
    )
    parser.add_argument(
        "--start",
        type=float,
        help="Start time in seconds"
    )
    parser.add_argument(
        "--end",
        type=float,
        help="End time in seconds"
    )
    parser.add_argument(
        "--prefix",
        default="frame",
        help="Filename prefix (default: frame)"
    )
    parser.add_argument(
        "--scale",
        help="Output resolution, e.g., '1920:1080' or '-1:720' (keep aspect ratio)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show video information and exit"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output including FFmpeg command"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    return parser


def main(args=None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command line arguments (for testing). If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Check FFmpeg installation
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in PATH.", file=sys.stderr)
        print("Install FFmpeg:", file=sys.stderr)
        print("  - macOS: brew install ffmpeg", file=sys.stderr)
        print("  - Ubuntu/Debian: sudo apt install ffmpeg", file=sys.stderr)
        print("  - Windows: Download from https://ffmpeg.org/download.html", file=sys.stderr)
        return 1

    # Check if video file exists
    video_path = Path(parsed_args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}", file=sys.stderr)
        return 1

    # Show video info
    info = get_video_info(parsed_args.video)
    if info:
        print("Video Information:")
        for line in str(info).split("\n"):
            print(f"  {line}")
        print()

    # Exit if only showing info
    if parsed_args.info:
        return 0

    # Extract frames
    try:
        print(f"Extracting frames from: {video_path}")
        print(f"Output directory: {parsed_args.output}")
        print(f"Settings: {parsed_args.fps} fps, {parsed_args.format.upper()} format, quality {parsed_args.quality}")
        print()

        frames = extract_frames(
            video_path=parsed_args.video,
            output_dir=parsed_args.output,
            fps=parsed_args.fps,
            format=parsed_args.format,
            quality=parsed_args.quality,
            start_time=parsed_args.start,
            end_time=parsed_args.end,
            prefix=parsed_args.prefix,
            scale=parsed_args.scale,
            verbose=parsed_args.verbose
        )

        frame_count = len(frames)
        if frame_count > 0:
            print(f"Successfully extracted {frame_count} frames to '{parsed_args.output}/'")
            return 0
        else:
            print("Warning: No frames were extracted. Check your settings.", file=sys.stderr)
            return 1

    except (FFmpegNotFoundError, VideoNotFoundError, ExtractionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
