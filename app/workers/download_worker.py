"""PyQt5 worker responsible for executing downloads off the UI thread."""

from PyQt5.QtCore import QThread, pyqtSignal

from app.services.youtube_service import YouTubeService


class DownloadWorker(QThread):
    """Execute one download operation in a background QThread."""

    progress = pyqtSignal(dict)
    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, url, output_directory, audio_format="mp3", quality="128K", parent=None):
        super().__init__(parent)
        self.url = url
        self.output_directory = output_directory
        self.audio_format = audio_format
        self.quality = quality

    def run(self):
        try:
            service = YouTubeService(self.output_directory)
            result = service.extract_audio(
                url=self.url,
                format=self.audio_format,
                quality=self.quality,
                progress_callback=self.progress.emit,
            )
            if result.get("success"):
                self.succeeded.emit(result)
            else:
                self.failed.emit(result.get("error", "Erro desconhecido durante o download."))
        except Exception as exc:
            self.failed.emit(str(exc))
