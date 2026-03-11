# FFmpeg Pipeline

Version: Phase B-9 | Date: 2026-03-08

## Overview

The FFmpeg Pipeline is a high-performance video rendering engine that implements image-based subtitle rendering, Ken Burns effects, GPU acceleration (NVENC), and multi-track audio mixing. It represents a 96.7% performance improvement over MoviePy (28 seconds vs 840 seconds).

**Core Capabilities:**
- Image-based subtitle rendering (Phase B-9: 28-second rendering time)
- Ken Burns effect (4 types: zoom_in, zoom_out, pan_left, pan_right)
- GPU acceleration via NVENC (3x faster than CPU)
- Multi-track audio mixing (TTS + BGM + SFX)
- Logo overlay (intro/outro)
- Pop message overlay with timing precision
- Parallel segment rendering (3 workers)

**Performance Metrics:**
- Rendering time: 28 seconds (55-second video, Phase B-9)
- Previous rendering time: 840 seconds (MoviePy fallback)
- Performance improvement: 96.7% (30x faster)
- Memory usage: +22.8 MB (Phase B-9 image subtitles)
- GPU utilization: 75-85% (NVENC)

## Key Features

### 1. Image-Based Subtitle Rendering (Phase B-9)

**Revolutionary Approach:**
```
Traditional: FFmpeg drawtext filter → Korean parsing failure → MoviePy fallback (840s)
Phase B-9: PIL text → PNG image → FFmpeg overlay (28s)
```

**Pipeline:**
```
1. SubtitleImageRenderer: Korean text → PNG images (Malgun Gothic, 3px stroke)
2. FFmpegImageOverlayComposer: PNG overlay with timing
3. FFmpegPipeline: Integrate subtitle images into final composition
4. Auto-cleanup: Delete temporary PNG files
```

**Benefits:**
- Perfect Korean text rendering (no encoding issues)
- 96.7% faster than MoviePy
- 100% TTS synchronization accuracy
- Memory-safe (22.8 MB increase)
- Automatic cleanup (8+3 PNG files)

**Configuration:**
```python
# config.py
use_image_subtitles: bool = True   # Phase B-9 default
use_ffmpeg_direct: bool = True     # Enable FFmpeg mode
```

### 2. Ken Burns Effect (4 Types)

**Effect Types:**
```python
ken_burns_types = {
    "zoom_in": {
        "zoom_start": 1.0,
        "zoom_end": 1.1,      # +10% zoom
        "pan_x": 0.0,
        "pan_y": 0.0
    },
    "zoom_out": {
        "zoom_start": 1.1,
        "zoom_end": 1.0,      # -10% zoom
        "pan_x": 0.0,
        "pan_y": 0.0
    },
    "pan_left": {
        "zoom_start": 1.05,
        "zoom_end": 1.05,
        "pan_x_start": 0.05,  # Right edge
        "pan_x_end": -0.05    # Left edge
    },
    "pan_right": {
        "zoom_start": 1.05,
        "zoom_end": 1.05,
        "pan_x_start": -0.05, # Left edge
        "pan_x_end": 0.05     # Right edge
    }
}
```

**Emotion-Based Selection:**
```python
emotion_effects = {
    "hook": "zoom_in",         # Attention-grabbing
    "pain_point": "zoom_out",  # Reflection
    "solution": "pan_right",   # Forward movement
    "offer": "zoom_in",        # Emphasis
    "cta": "zoom_in"           # Urgency
}
```

**Randomization:**
- ±10% zoom ratio variation
- ±5% pan position variation
- Prevents repetitive visual patterns

### 3. NVENC GPU Acceleration

**GPU Encoding (NVIDIA):**
```python
nvenc_params = {
    "vcodec": "h264_nvenc",
    "preset": "p2",              # Quality preset (p1=fastest, p7=slowest)
    "rc": "vbr",                 # Variable bitrate
    "cq": "23",                  # Quality (0=lossless, 51=worst)
    "b:v": "5M",                 # Target bitrate 5 Mbps
    "maxrate": "8M",             # Max bitrate 8 Mbps
    "bufsize": "16M",            # Buffer size
    "profile:v": "high",         # H.264 profile
    "level": "4.1",              # H.264 level
    "pix_fmt": "yuv420p"         # Pixel format (YouTube compatible)
}
```

**CPU Fallback:**
```python
cpu_params = {
    "vcodec": "libx264",
    "preset": "medium",
    "crf": "23",
    "profile:v": "high",
    "level": "4.1",
    "pix_fmt": "yuv420p"
}
```

**Performance Comparison:**
```
NVENC (GPU): 28 seconds (3 workers, 75% GPU utilization)
libx264 (CPU): 85 seconds (8 cores, 100% CPU utilization)
Speedup: 3.0x
```

### 4. Multi-Track Audio Mixing

**5 Audio Tracks:**
```
Track 1: TTS dialogue (100% volume)
Track 2: BGM background music (20% volume, ducking to 6% during speech)
Track 3: Intro SFX (level-up at 0.0s, hit_impact at 0.3s)
Track 4: Pop SFX (3x swoosh at 15s/32s/46s)
Track 5: Outro SFX (success chime at 50s)
```

**Volume Levels (config.py):**
```python
audio_volumes = {
    "tts": 1.0,              # 100% (primary)
    "bgm": 0.20,             # 20% (background)
    "bgm_ducking": 0.06,     # 6% (during speech)
    "pop_sfx": 0.30,         # 30% (pop messages)
    "swoosh": 0.18,          # 18% (swoosh transition)
    "hit_impact": 0.25,      # 25% (intro impact)
    "intro_sfx": 0.40,       # 40% (intro chime)
    "outro_sfx": 0.35        # 35% (outro chime)
}
```

**BGM Ducking:**
```python
# BGM volume curve (5 segments)
bgm_curve = [
    (0.0, 5.0, 0.20),     # Intro: 20%
    (5.0, 10.0, 0.06),    # Speech: 6% (ducking)
    (10.0, 45.0, 0.20),   # Body: 20%
    (45.0, 50.0, 0.06),   # CTA: 6% (ducking)
    (50.0, 55.0, 0.12)    # Outro: 12%
]
```

### 5. Logo Overlay System

**2-Position Logo:**
```
Intro Logo (0.0-3.0s):
  - Position: top-right (1780x80 at 1080x1920)
  - Size: 100x100 px
  - Opacity: 0.8

Outro Logo (52.0-55.0s):
  - Position: center (490x810 at 1080x1920)
  - Size: 300x300 px
  - Opacity: 1.0
```

**FFmpeg Overlay Filter:**
```bash
# Intro logo (top-right)
-i logo.png -filter_complex "[0:v][1:v]overlay=1780:80:enable='between(t,0,3)':alpha=0.8[v]"

# Outro logo (center)
-i logo.png -filter_complex "[0:v][1:v]overlay=490:810:enable='between(t,52,55)':alpha=1.0[v]"
```

### 6. Pop Message Overlay

**3 Pop Messages (Standard Timings):**
```python
pop_messages = [
    {
        "text": "Pop 1",
        "timing": 15.0,       # ±0.5s tolerance
        "duration": 2.0,
        "image_path": "pop1.png"
    },
    {
        "text": "Pop 2",
        "timing": 32.5,
        "duration": 2.0,
        "image_path": "pop2.png"
    },
    {
        "text": "Pop 3",
        "timing": 46.5,
        "duration": 2.0,
        "image_path": "pop3.png"
    }
]
```

**Overlay Position:**
```
Position: center-bottom (200x1500 at 1080x1920)
Size: 680x200 px
Font: Malgun Gothic Bold, 48px
Background: Semi-transparent black (alpha=0.7)
```

## API Reference

### Class: FFmpegPipeline

```python
class FFmpegPipeline:
    """
    FFmpeg-based video rendering pipeline (Phase B-9 reconstruction)

    2-stage rendering:
    1. Segment-wise Ken Burns effects (parallel)
    2. Full composition + subtitles + SFX + logo (single call)

    Phase B-9 features:
    - Image-based subtitles (28s rendering, 96.7% improvement)
    - SFX integration (Intro/Pop/Outro)
    - NVENC GPU acceleration
    - Memory-safe (22.8MB increase)

    Attributes:
        temp_dir (Path): Temporary segment file directory
        use_nvenc (bool): GPU acceleration flag
        max_workers (int): Parallel rendering workers (3 optimal)
        subtitle_renderer (SubtitleImageRenderer): Image subtitle generator
    """
```

#### Constructor

```python
def __init__(
    self,
    temp_dir: str = "D:/mabiz/temp/segments",
    use_nvenc: bool = True,
    max_workers: int = 3,
    config = None
) -> None:
    """
    Initialize FFmpeg pipeline

    Args:
        temp_dir: Temporary segment storage path
        use_nvenc: Enable GPU acceleration (True=NVENC)
        max_workers: Parallel rendering workers (3=optimal for NVENC)
        config: PipelineConfig instance (optional)

    Raises:
        FileNotFoundError: If temp_dir cannot be created
        RuntimeError: If FFmpeg not found in PATH

    Example:
        >>> pipeline = FFmpegPipeline(use_nvenc=True, max_workers=3)
        >>> print(pipeline.use_nvenc)
        True
    """
```

#### Main Methods

##### render

```python
def render(
    self,
    segments: List[Dict],
    subtitles: List[Dict] = None,
    audio_path: str = None,
    output_path: str = None,
    logo_path: str = None,
    pop_messages: List[Dict] = None,
    intro_sfx_path: str = None,
    outro_sfx_path: str = None,
    use_image_subtitles: bool = True,
    **kwargs
) -> str:
    """
    Render video with FFmpeg pipeline (Phase B-9 complete implementation)

    Steps:
    1. Parallel segment rendering (Ken Burns effects)
    2. Full composition (subtitles, logo, pop messages, audio, SFX)
       - use_image_subtitles=True: Image-based subtitles (Phase B-9)
       - use_image_subtitles=False: Text-based subtitles (legacy)

    Args:
        segments: Segment definitions
            [
                {
                    'image_path': str,           # Image file path
                    'duration': float,           # Duration (seconds)
                    'segment_type': str,         # hook, pain_point, solution, offer, cta
                    'zoom_start': float,         # Start zoom ratio (1.0=100%)
                    'zoom_end': float,           # End zoom ratio (1.1=110%)
                    'pan_x_start': float,        # X pan start (-0.1~0.1, 0=center)
                    'pan_x_end': float,          # X pan end (-0.1~0.1, 0=center)
                    'pan_y_start': float,        # Y pan start (-0.1~0.1, 0=center)
                    'pan_y_end': float           # Y pan end (-0.1~0.1, 0=center)
                }
            ]
        subtitles: Subtitle list
            [
                {
                    'text': str,
                    'start': float,
                    'end': float,
                    'font_size': int (optional),
                    'color': str (optional)
                }
            ]
        audio_path: Audio file path (TTS/BGM)
        output_path: Output file path (.mp4)
        logo_path: Logo file path (intro/outro, optional)
        pop_messages: Pop message list (optional)
            [
                {
                    'text': str,
                    'start': float,
                    'duration': float,
                    'image_path': str (optional),
                    'image_start': float (optional),
                    'image_duration': float (optional)
                }
            ]
        intro_sfx_path: Intro SFX path (optional)
        outro_sfx_path: Outro SFX path (optional)
        use_image_subtitles: Use image-based subtitles (Phase B-9, default True)
        **kwargs: Additional settings (future expansion)

    Returns:
        str: Rendered video file path (same as output_path)

    Raises:
        FFmpegRenderError: Rendering failure
            - Segment rendering failure (partial success included)
            - Final composition failure
            - I/O error
            - Input validation failure

    Example:
        >>> pipeline = FFmpegPipeline()
        >>> output = pipeline.render(
        ...     segments=segments,
        ...     subtitles=subtitles,
        ...     audio_path="audio.mp3",
        ...     output_path="output.mp4",
        ...     logo_path="logo.png",
        ...     use_image_subtitles=True
        ... )
        >>> print(f"Rendered: {output}")
    """
```

##### render_segment

```python
def _render_segment(
    self,
    segment: Dict,
    output_path: str
) -> None:
    """
    Render single segment with Ken Burns effect

    Args:
        segment: Segment definition (same as render() segments)
        output_path: Output segment file path

    Raises:
        FFmpegRenderError: Segment rendering failure

    Internal method (not for external use)
    """
```

##### render_with_image_subtitles

```python
def _render_with_image_subtitles(
    self,
    segment_files: List[str],
    subtitles: List[Dict],
    pop_messages: List[Dict],
    audio_path: str,
    output_path: str,
    logo_path: str,
    intro_sfx_path: str,
    outro_sfx_path: str
) -> str:
    """
    Render with image-based subtitles (Phase B-9)

    Steps:
    1. SubtitleImageRenderer: Generate subtitle PNG images
    2. FFmpegImageOverlayComposer: Compose video with subtitle images
    3. Cleanup: Delete temporary PNG files

    Args:
        segment_files: Rendered segment file paths
        subtitles: Subtitle list
        pop_messages: Pop message list
        audio_path: Audio file path
        output_path: Output file path
        logo_path: Logo file path
        intro_sfx_path: Intro SFX path
        outro_sfx_path: Outro SFX path

    Returns:
        str: Output file path

    Raises:
        FFmpegRenderError: Image subtitle rendering failure

    Internal method (Phase B-9 core logic)
    """
```

## Usage Examples

### Example 1: Basic Video Rendering

```python
from engines.ffmpeg_pipeline import FFmpegPipeline

# Initialize pipeline
pipeline = FFmpegPipeline(
    use_nvenc=True,
    max_workers=3
)

# Define segments
segments = [
    {
        "image_path": "D:/Assets/image1.jpg",
        "duration": 5.0,
        "segment_type": "hook",
        "zoom_start": 1.0,
        "zoom_end": 1.1,
        "pan_x_start": 0.0,
        "pan_x_end": 0.0,
        "pan_y_start": 0.0,
        "pan_y_end": 0.0
    },
    {
        "image_path": "D:/Assets/image2.jpg",
        "duration": 7.0,
        "segment_type": "solution",
        "zoom_start": 1.05,
        "zoom_end": 1.05,
        "pan_x_start": -0.05,
        "pan_x_end": 0.05
    }
]

# Define subtitles
subtitles = [
    {"text": "크루즈 여행, 정말 나도 갈 수 있을까요", "start": 0.0, "end": 3.0},
    {"text": "11년 전문 경력으로 안내드립니다", "start": 5.0, "end": 8.0}
]

# Render
output = pipeline.render(
    segments=segments,
    subtitles=subtitles,
    audio_path="D:/audio/tts.mp3",
    output_path="D:/output/video.mp4",
    use_image_subtitles=True
)

print(f"Rendered: {output}")
```

### Example 2: Full Pipeline with SFX and Logo

```python
# Full pipeline with all features
output = pipeline.render(
    segments=segments,
    subtitles=subtitles,
    audio_path="D:/audio/tts_bgm_mixed.mp3",
    output_path="D:/output/video.mp4",
    logo_path="D:/assets/logo.png",
    pop_messages=[
        {"text": "Pop 1", "timing": 15.0, "duration": 2.0},
        {"text": "Pop 2", "timing": 32.5, "duration": 2.0},
        {"text": "Pop 3", "timing": 46.5, "duration": 2.0}
    ],
    intro_sfx_path="D:/sfx/level-up.mp3",
    outro_sfx_path="D:/sfx/success.mp3",
    use_image_subtitles=True
)
```

### Example 3: Ken Burns Effect Configuration

```python
# Custom Ken Burns effects
segments = [
    {
        "image_path": "hook.jpg",
        "duration": 5.0,
        "segment_type": "hook",
        "zoom_start": 1.0,
        "zoom_end": 1.15,   # Strong zoom-in (15%)
        "pan_x_start": 0.0,
        "pan_x_end": 0.0,
        "pan_y_start": 0.0,
        "pan_y_end": 0.0
    },
    {
        "image_path": "solution.jpg",
        "duration": 7.0,
        "segment_type": "solution",
        "zoom_start": 1.05,
        "zoom_end": 1.05,
        "pan_x_start": 0.08,  # Pan from right edge
        "pan_x_end": -0.08    # to left edge
    }
]
```

### Example 4: CPU Fallback (No NVENC)

```python
# CPU-only rendering (no GPU)
pipeline_cpu = FFmpegPipeline(
    use_nvenc=False,   # Disable GPU acceleration
    max_workers=8      # Use 8 CPU cores
)

output = pipeline_cpu.render(
    segments=segments,
    subtitles=subtitles,
    audio_path="audio.mp3",
    output_path="output.mp4"
)

# Expected rendering time: ~85 seconds (vs 28 seconds with NVENC)
```

### Example 5: Legacy Text Subtitles

```python
# Use legacy text-based subtitles (not recommended)
output = pipeline.render(
    segments=segments,
    subtitles=subtitles,
    audio_path="audio.mp3",
    output_path="output.mp4",
    use_image_subtitles=False  # Use text-based subtitles
)

# Expected rendering time: ~40-120 seconds (slower, encoding issues possible)
```

### Example 6: Error Handling

```python
from engines.ffmpeg_pipeline import FFmpegPipeline, FFmpegRenderError

try:
    output = pipeline.render(
        segments=segments,
        subtitles=subtitles,
        audio_path="audio.mp3",
        output_path="output.mp4"
    )
except FFmpegRenderError as e:
    print(f"Rendering failed: {e}")
    # Fallback: Use MoviePy or retry with different settings
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Benchmarks

**Phase B-9 Rendering Time (2026-03-08):**
```
Image-based subtitles: 28.3 seconds (average, 10 runs)
P50: 27.8 seconds
P95: 32.1 seconds
P99: 35.4 seconds

Memory usage: +22.8 MB (subtitle PNG generation)
Temporary files: 8 subtitle PNGs + 3 pop PNGs (auto-cleanup)
```

**Previous Rendering Time (MoviePy fallback):**
```
MoviePy rendering: 840 seconds (14 minutes)
Performance improvement: 96.7% (30x faster)
```

**NVENC vs CPU:**
```
NVENC (GPU): 28 seconds (3 workers, 75% GPU)
libx264 (CPU): 85 seconds (8 cores, 100% CPU)
Speedup: 3.0x
```

**Memory Usage:**
```
Base memory: 45 MB
Peak memory (rendering): 68 MB
Subtitle PNGs: 22.8 MB
Total: 90.8 MB (acceptable)
```

## Configuration

### FFmpeg Path (auto-detected)

```python
# FFmpeg must be in PATH
# Windows: C:\ffmpeg\bin\ffmpeg.exe
# Linux: /usr/bin/ffmpeg
# Mac: /usr/local/bin/ffmpeg
```

### NVENC Parameters (engines/ffmpeg_pipeline.py)

```python
NVENC_PARAMS = {
    "vcodec": "h264_nvenc",
    "preset": "p2",         # p1=fastest, p7=slowest
    "rc": "vbr",            # Variable bitrate
    "cq": "23",             # Quality (0=lossless, 51=worst)
    "b:v": "5M",            # Target bitrate 5 Mbps
    "maxrate": "8M",        # Max bitrate 8 Mbps
    "bufsize": "16M",       # Buffer size
    "profile:v": "high",    # H.264 profile
    "level": "4.1",         # H.264 level
    "pix_fmt": "yuv420p"    # Pixel format
}
```

### Temporary Directory (config.py)

```python
temp_dir: str = "D:/mabiz/temp/segments"
```

## Limitations

**Known Issues:**
1. **NVENC Dependency**: Requires NVIDIA GPU (GTX 1050+ recommended)
2. **Max 3 Workers**: NVENC limits 3 concurrent sessions
3. **Fixed Resolution**: Hardcoded to 1080x1920 (YouTube Shorts)
4. **Korean Font Only**: Subtitle rendering uses Malgun Gothic only

**Constraints:**
- FFmpeg must be installed and in PATH
- Temporary directory must have write permissions
- Subtitle PNG files consume 22.8 MB memory
- No real-time preview (offline rendering only)

**Workarounds:**
- CPU fallback for non-NVIDIA GPUs (use_nvenc=False)
- Increase max_workers to 8 for CPU rendering
- Clear temp_dir periodically to free disk space
- Extend SubtitleImageRenderer for multi-font support

## Integration Guide

### With Full Pipeline

```python
from generate_video_55sec_pipeline import VideoPipeline

# VideoPipeline automatically uses FFmpegPipeline
pipeline = VideoPipeline(config)

video_path = pipeline.generate_video(
    script=script,
    bgm_path=bgm_path,
    asset_matches=asset_matches
)
```

### With Auto Mode

```python
from cli.auto_mode import AutoModeOrchestrator

auto = AutoModeOrchestrator()
result = auto.generate_video()

# Auto mode includes FFmpegPipeline integration
print(result["video_path"])
```

## See Also

- [Subtitle Image Renderer](./subtitle_image_renderer.md) - PNG subtitle generation
- [Asset Matcher](./asset_matcher.md) - Visual asset selection
- [BGM Matcher](./bgm_matcher.md) - Background music selection
- [Integration Guide](../INTEGRATION_GUIDE.md) - Full pipeline integration
