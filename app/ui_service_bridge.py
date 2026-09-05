"""Compatibility bridge that routes legacy UI threads through YouTubeService.

This keeps the current PyQt5 windows unchanged while removing their direct
yt-dlp download/conversion path from the active application flow.
"""

from app.services.youtube_service import YouTubeService
from single_video_window import AudioExtractorThread
from playlist_window import PlaylistExtractorThread


def _extract_audio_with_progress(self, url, output_directory=None, format="mp3", quality="128K"):
    service = YouTubeService(output_directory)

    def progress_callback(data):
        status = data.get("status")
        if status == "downloading":
            percent = service._percent(data)
            percent_str = data.get("_percent_str", f"{percent}%")
            self.progress_signal.emit(f"Baixando: {percent_str}")
            self.progress_percentage_signal.emit(percent)
        elif status == "finished":
            self.progress_signal.emit("Download concluído, processando...")
            self.progress_percentage_signal.emit(100)

    return service.extract_audio(
        url=url,
        format=format,
        quality=quality,
        progress_callback=progress_callback,
    )


def install():
    """Patch the legacy thread methods to use the centralized service."""
    AudioExtractorThread.extract_audio_with_progress = _extract_audio_with_progress
    PlaylistExtractorThread.extract_audio_with_progress = _extract_audio_with_progress
