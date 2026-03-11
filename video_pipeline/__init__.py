"""
Video Pipeline Module

High-performance video production pipeline.

Main Modules:
- config: VideoConfig configuration class
- rendering: Video rendering engines
- effects: Visual effects processors
- audio: Audio processing

Usage:
    from video_pipeline import VideoConfig
    config = VideoConfig()
"""

# Core configuration
try:
    from .config import VideoConfig
except ImportError:
    pass

# Version
__version__ = "5.0.0"


def get_version():
    """Get package version"""
    return __version__


__all__ = [
    "VideoConfig",
    "get_version",
]
