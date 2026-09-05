"""PyQt5 workers for metadata inspection and background downloads."""

import threading

from PyQt5.QtCore import QThread, pyqtSignal

import yt_dlp

from app.services.youtube_service import DownloadCancelled, YouTubeService


class DownloadWorker(QThread):
    """Execute one download operation in a background QThread."""

    progress = pyqtSignal(dict)
    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, url, output_directory, audio_format="mp3", quality="128K", parent=None):
        super().__init__(parent)
        self.url = url
        self.output_directory = output_directory
        self.audio_format = audio_format
        self.quality = quality
        self._cancel_event = threading.Event()

    def cancel(self):
        """Request a cooperative cancellation of the active yt-dlp operation."""
        self._cancel_event.set()

    def is_cancel_requested(self):
        return self._cancel_event.is_set()

    def run(self):
        try:
            service = YouTubeService(self.output_directory)
            result = service.extract_audio(
                url=self.url,
                format=self.audio_format,
                quality=self.quality,
                progress_callback=self.progress.emit,
                cancellation_callback=self.is_cancel_requested,
            )
            if result.get("cancelled"):
                self.cancelled.emit()
            elif result.get("success"):
                self.succeeded.emit(result)
            else:
                self.failed.emit(result.get("error", "Erro desconhecido durante o download."))
        except DownloadCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class MetadataWorker(QThread):
    """Fetch YouTube metadata without blocking the Qt UI thread."""

    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, url, single=False, parent=None):
        super().__init__(parent)
        self.url = url
        self.single = single

    def run(self):
        try:
            options = {
                "quiet": True,
                "noplaylist": self.single,
                "extract_flat": not self.single,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(self.url, download=False)
            self.succeeded.emit(info)
        except Exception as exc:
            self.failed.emit(str(exc))
