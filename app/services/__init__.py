"""Application services.

The YouTube service is imported lazily to avoid circular imports between
service modules such as AudioConverter and FFmpegManager.
"""

__all__ = ["YouTubeService"]


def __getattr__(name: str):
    """Load services lazily while preserving the public package API."""
    if name == "YouTubeService":
        from .youtube_service import YouTubeService

        return YouTubeService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
