"""
Tests for video2frames extractor module.
"""

import pytest
from pathlib import Path

from video2frames import extract_frames, get_video_info, check_ffmpeg, __version__
from video2frames.extractor import VideoInfo, FFmpegNotFoundError, VideoNotFoundError


def test_version():
    """Test that version is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_check_ffmpeg():
    """Test FFmpeg availability check."""
    result = check_ffmpeg()
    assert isinstance(result, bool)


def test_video_info_str():
    """Test VideoInfo string representation."""
    info = VideoInfo(width=1920, height=1080, fps=30.0, duration=60.0)
    info_str = str(info)
    assert "1920x1080" in info_str
    assert "30.00 fps" in info_str
    assert "60.00 seconds" in info_str


def test_video_info_total_frames():
    """Test VideoInfo total_frames calculation."""
    info = VideoInfo(width=1920, height=1080, fps=30.0, duration=10.0)
    assert info.total_frames == 300


def test_video_info_no_duration():
    """Test VideoInfo without duration."""
    info = VideoInfo(width=1920, height=1080, fps=30.0)
    assert info.total_frames is None


def test_get_video_info_not_found():
    """Test get_video_info with non-existent file."""
    with pytest.raises(VideoNotFoundError):
        get_video_info("/nonexistent/video.mp4")


def test_extract_frames_video_not_found():
    """Test extract_frames with non-existent file."""
    with pytest.raises((VideoNotFoundError, FFmpegNotFoundError)):
        extract_frames("/nonexistent/video.mp4")


def test_extract_frames_invalid_format():
    """Test extract_frames with invalid format."""
    # This test requires a valid video file, skip if FFmpeg not available
    if not check_ffmpeg():
        pytest.skip("FFmpeg not available")

    with pytest.raises(ValueError, match="Unsupported format"):
        extract_frames("video.mp4", format="invalid")
