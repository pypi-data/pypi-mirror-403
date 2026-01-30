"""
Core video frame extraction functionality using FFmpeg.
"""

import subprocess
import shutil
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class VideoInfo:
    """Video metadata information."""
    width: int
    height: int
    fps: float
    duration: Optional[float] = None

    @property
    def total_frames(self) -> Optional[int]:
        """Estimated total frames in the video."""
        if self.duration:
            return int(self.duration * self.fps)
        return None

    def __str__(self) -> str:
        lines = [
            f"Resolution: {self.width}x{self.height}",
            f"Frame Rate: {self.fps:.2f} fps",
        ]
        if self.duration:
            lines.append(f"Duration: {self.duration:.2f} seconds")
            if self.total_frames:
                lines.append(f"Total Frames: ~{self.total_frames}")
        return "\n".join(lines)


class FFmpegNotFoundError(Exception):
    """Raised when FFmpeg is not installed or not in PATH."""
    pass


class VideoNotFoundError(Exception):
    """Raised when the video file does not exist."""
    pass


class ExtractionError(Exception):
    """Raised when frame extraction fails."""
    pass


def check_ffmpeg() -> bool:
    """
    Check if FFmpeg is installed and accessible.

    Returns:
        True if FFmpeg is available, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


def get_video_info(video_path: str) -> Optional[VideoInfo]:
    """
    Get video information using ffprobe.

    Args:
        video_path: Path to the video file.

    Returns:
        VideoInfo object with video metadata, or None if unable to read.

    Raises:
        VideoNotFoundError: If the video file does not exist.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise VideoNotFoundError(f"Video file not found: {video_path}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-of", "csv=p=0",
        str(video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split(",")
        if len(parts) >= 3:
            width = int(parts[0])
            height = int(parts[1])
            # Parse frame rate (e.g., "30/1" or "30000/1001")
            fps_parts = parts[2].split("/")
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])
            duration = float(parts[3]) if len(parts) > 3 and parts[3] else None
            return VideoInfo(
                width=width,
                height=height,
                fps=fps,
                duration=duration
            )
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass

    return None


def extract_frames(
    video_path: str,
    output_dir: str = "frames",
    fps: float = 1.0,
    format: str = "jpg",
    quality: int = 90,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    prefix: str = "frame",
    scale: Optional[str] = None,
    overwrite: bool = True,
    verbose: bool = False
) -> List[Path]:
    """
    Extract frames from video using FFmpeg.

    Args:
        video_path: Path to input video file.
        output_dir: Directory to save extracted frames.
        fps: Frames per second to extract (default: 1.0).
        format: Output format - 'jpg', 'png', or 'webp' (default: 'jpg').
        quality: Image quality 1-100 (default: 90).
        start_time: Start time in seconds (optional).
        end_time: End time in seconds (optional).
        prefix: Filename prefix for output frames (default: 'frame').
        scale: Output resolution as "width:height" (optional, e.g., "1920:1080" or "-1:720").
        overwrite: Whether to overwrite existing files (default: True).
        verbose: Print FFmpeg command and output (default: False).

    Returns:
        List of paths to extracted frame files.

    Raises:
        FFmpegNotFoundError: If FFmpeg is not installed.
        VideoNotFoundError: If the video file does not exist.
        ExtractionError: If frame extraction fails.
        ValueError: If an invalid format is specified.
    """
    if not check_ffmpeg():
        raise FFmpegNotFoundError(
            "FFmpeg is not installed or not in PATH.\n"
            "Install FFmpeg:\n"
            "  - macOS: brew install ffmpeg\n"
            "  - Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  - Windows: Download from https://ffmpeg.org/download.html"
        )

    video_path = Path(video_path)
    output_dir = Path(output_dir)

    if not video_path.exists():
        raise VideoNotFoundError(f"Video file not found: {video_path}")

    # Validate format
    format = format.lower()
    if format == "jpeg":
        format = "jpg"
    if format not in ("jpg", "png", "webp"):
        raise ValueError(f"Unsupported format: {format}. Use 'jpg', 'png', or 'webp'.")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build FFmpeg command
    cmd = ["ffmpeg"]
    if overwrite:
        cmd.append("-y")

    # Input time range (before -i for faster seeking)
    if start_time is not None:
        cmd.extend(["-ss", str(start_time)])

    # Input file
    cmd.extend(["-i", str(video_path)])

    # End time (after -i)
    if end_time is not None:
        if start_time is not None:
            duration = end_time - start_time
            cmd.extend(["-t", str(duration)])
        else:
            cmd.extend(["-t", str(end_time)])

    # Video filters
    filters = [f"fps={fps}"]
    if scale:
        filters.append(f"scale={scale}")
    cmd.extend(["-vf", ",".join(filters)])

    # Output format and quality settings
    if format == "jpg":
        ext = "jpg"
        # FFmpeg uses 1-31 for JPEG quality, lower is better
        q_value = int((100 - quality) * 31 / 100 + 1)
        cmd.extend(["-q:v", str(q_value)])
    elif format == "png":
        ext = "png"
        # PNG compression level (0-9, higher = more compression but slower)
        compression = int((100 - quality) * 9 / 100)
        cmd.extend(["-compression_level", str(compression)])
    else:  # webp
        ext = "webp"
        cmd.extend(["-quality", str(quality)])

    # Output pattern
    output_pattern = output_dir / f"{prefix}_%04d.{ext}"
    cmd.append(str(output_pattern))

    if verbose:
        print(f"Running: {' '.join(cmd)}")

    # Run FFmpeg
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        if verbose and result.stderr:
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        raise ExtractionError(f"FFmpeg extraction failed: {e.stderr}")

    # Return list of extracted frames
    frame_files = sorted(output_dir.glob(f"{prefix}_*.{ext}"))
    return frame_files
