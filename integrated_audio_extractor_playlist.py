"""Backward-compatible facade for the centralized YouTube service."""

import yt_dlp

from app.services.youtube_service import YouTubeService


def extract_audio_from_url(url, output_directory=None, format="mp3", quality="128K", progress_callback=None):
    """Compatibility wrapper used by the existing UI.

    New code should call :class:`YouTubeService` directly.
    """
    service = YouTubeService(output_directory)
    return service.extract_audio(
        url=url,
        format=format,
        quality=quality,
        progress_callback=progress_callback,
    )


def list_formats(video_url):
    """List formats exposed by yt-dlp for a URL."""
    with yt_dlp.YoutubeDL({"listformats": True}) as ydl:
        return ydl.extract_info(video_url, download=False)


def extract_audio_playlist(playlist_url, output_path=".", format="mp3", quality="128K"):
    """Compatibility wrapper for playlist extraction."""
    service = YouTubeService(output_path)
    return service.extract_audio(playlist_url, format=format, quality=quality)


if __name__ == "__main__":
    result = extract_audio_from_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        format="mp3",
        quality="192K",
    )
    print(result)
