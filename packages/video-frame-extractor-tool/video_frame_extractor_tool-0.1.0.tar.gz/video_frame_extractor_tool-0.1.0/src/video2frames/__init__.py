"""
video2frames - Extract frames from videos using FFmpeg

A command-line tool and Python library to extract frames from video files.
"""

__version__ = "0.1.0"
__author__ = "VideoToJPG"

from .extractor import extract_frames, get_video_info, check_ffmpeg

__all__ = ["extract_frames", "get_video_info", "check_ffmpeg", "__version__"]
