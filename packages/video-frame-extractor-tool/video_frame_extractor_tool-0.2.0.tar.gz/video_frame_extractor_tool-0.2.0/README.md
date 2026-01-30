# Video Frame Extractor Tool

A powerful **video frame extractor** command-line tool and Python library to extract frames from video files using FFmpeg.

[![PyPI version](https://badge.fury.io/py/video-frame-extractor-tool.svg)](https://pypi.org/project/video-frame-extractor-tool/)
[![GitHub](https://img.shields.io/github/stars/Video-Frame-Extractor/Video-Frame-Extractor-Tool?style=social)](https://github.com/Video-Frame-Extractor/Video-Frame-Extractor-Tool)

## Why Use This Video Frame Extractor?

This **video frame extractor** tool makes it easy to extract frames from any video file. Whether you need to create thumbnails, analyze video content, or build training datasets, this video frame extractor provides a simple yet powerful solution.

## Video Frame Extractor Features

- **Extract frames** at custom frame rates (e.g., 1 fps, 5 fps, or original)
- Support for multiple output formats: **JPG**, **PNG**, **WebP**
- Adjustable image quality settings for the video frame extractor output
- Extract frames from specific time ranges
- Resize/scale output frames
- Simple CLI and Python API for video frame extraction
- No Python dependencies (uses built-in modules only)

## Requirements for Video Frame Extractor

- Python 3.7+
- FFmpeg installed and available in PATH

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Install Video Frame Extractor

```bash
pip install video-frame-extractor-tool
```

## Video Frame Extractor Quick Start

### Command Line Video Frame Extractor

```bash
# Extract 1 frame per second as JPG (default)
video2frames video.mp4 -o frames/

# Extract at 5 fps as PNG
video2frames video.mp4 -o frames/ -f 5 --format png

# Extract frames from 10s to 30s
video2frames video.mp4 -o frames/ --start 10 --end 30

# Show video information
video2frames video.mp4 --info
```

### Python Video Frame Extractor API

```python
from video2frames import extract_frames, get_video_info

# Get video information
info = get_video_info("video.mp4")
print(f"Resolution: {info.width}x{info.height}")
print(f"Duration: {info.duration} seconds")
print(f"FPS: {info.fps}")

# Extract frames using video frame extractor
frames = extract_frames(
    "video.mp4",
    output_dir="frames",
    fps=2,
    format="png",
    quality=95
)
print(f"Extracted {len(frames)} frames")
```

## Video Frame Extractor CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `video` | Path to input video file | (required) |
| `-o, --output` | Output directory for extracted frames | `frames` |
| `-f, --fps` | Frames per second to extract | `1` |
| `--format` | Output format: `jpg`, `png`, `webp` | `jpg` |
| `-q, --quality` | Image quality (1-100) | `90` |
| `--start` | Start time in seconds | None |
| `--end` | End time in seconds | None |
| `--prefix` | Filename prefix for extracted frames | `frame` |
| `--scale` | Output resolution (e.g., `-1:720`) | None |
| `--info` | Show video info and exit | False |
| `-v, --verbose` | Verbose output | False |

## Video Frame Extractor Examples

### Extract Frames at Different Frame Rates

Use the video frame extractor to extract frames at various rates:

```bash
# 1 frame per second (good for long videos)
video2frames video.mp4 -o frames/ -f 1

# 5 frames per second
video2frames video.mp4 -o frames/ -f 5

# Original frame rate (e.g., 30 fps)
video2frames video.mp4 -o frames/ -f 30
```

### Video Frame Extractor Output Formats

The video frame extractor supports multiple output formats:

```bash
# JPEG (smaller files)
video2frames video.mp4 -o frames/ --format jpg

# PNG (lossless quality)
video2frames video.mp4 -o frames/ --format png

# WebP (modern format, good compression)
video2frames video.mp4 -o frames/ --format webp
```

### Extract Frames from Specific Time Range

```bash
# Extract frames from 1:00 to 2:00
video2frames video.mp4 -o frames/ --start 60 --end 120

# First 30 seconds only
video2frames video.mp4 -o frames/ --end 30
```

### Resize Extracted Frames

```bash
# Resize to 720p (keep aspect ratio)
video2frames video.mp4 -o frames/ --scale -1:720

# Resize to specific dimensions
video2frames video.mp4 -o frames/ --scale 1280:720
```

### Batch Video Frame Extraction

Process multiple videos with the video frame extractor:

```bash
# Process multiple videos
for video in *.mp4; do
    video2frames "$video" -o "${video%.mp4}_frames/"
done
```

## Video Frame Extractor Python API Reference

### `extract_frames()`

The main function of the video frame extractor:

```python
extract_frames(
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
) -> List[Path]
```

### `get_video_info()`

Get video information before using the video frame extractor:

```python
get_video_info(video_path: str) -> Optional[VideoInfo]
```

Returns a `VideoInfo` object with:
- `width`: Video width in pixels
- `height`: Video height in pixels
- `fps`: Frame rate
- `duration`: Duration in seconds
- `total_frames`: Estimated total frames

### `check_ffmpeg()`

Check if FFmpeg is available for the video frame extractor:

```python
check_ffmpeg() -> bool
```

Returns `True` if FFmpeg is available.

## Video Frame Extractor Use Cases

- **Create video thumbnails** - Extract key frames for video previews
- **Build ML training datasets** - Use the video frame extractor to create image datasets from videos
- **Video analysis** - Extract frames for motion analysis or quality inspection
- **Content creation** - Get still images from video content
- **Documentation** - Create step-by-step screenshots from tutorial videos

## License

MIT License - see [LICENSE](LICENSE) file.

## Links

- **GitHub**: [Video-Frame-Extractor/Video-Frame-Extractor-Tool](https://github.com/Video-Frame-Extractor/Video-Frame-Extractor-Tool)
- **PyPI**: [video-frame-extractor-tool](https://pypi.org/project/video-frame-extractor-tool/)
- **Online Tool**: [VideoToJPG.com](https://videotojpg.com) - Online video frame extractor with sharpness detection
- **FFmpeg**: [ffmpeg.org](https://ffmpeg.org) - The multimedia framework powering this video frame extractor
