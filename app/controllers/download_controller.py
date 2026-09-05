"""Controller that coordinates UI requests and background download workers."""

from PyQt5.QtCore import QObject, pyqtSignal

import yt_dlp

from app.services.youtube_service import YouTubeService
from app.workers.download_worker import DownloadWorker


class DownloadController(QObject):
    """Application-facing API for metadata inspection and audio downloads."""

    progress = pyqtSignal(dict)
    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None

    @staticmethod
    def validate(url, audio_format="mp3", quality="128K"):
        url = (url or "").strip()
        if not url:
            return False, "URL não informada."
        if "youtube.com" not in url and "youtu.be" not in url:
            return False, "Por favor, insira uma URL válida do YouTube."
        if audio_format.lower() not in YouTubeService.SUPPORTED_FORMATS:
            return False, f"Formato não suportado: {audio_format}"
        normalized_quality = YouTubeService._normalize_quality(quality)
        if normalized_quality not in {"64K", "128K", "192K", "320K"}:
            return False, f"Qualidade não suportada: {normalized_quality}"
        return True, ""

    def inspect(self, url, single=True):
        """Fetch metadata without downloading media."""
        url = (url or "").strip()
        if not url:
            raise ValueError("URL não informada.")
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": not single}) as ydl:
            return ydl.extract_info(url, download=False)

    def download(self, url, output_directory, audio_format="mp3", quality="128K"):
        """Start a background download and return the worker."""
        valid, error = self.validate(url, audio_format, quality)
        if not valid:
            self.failed.emit(error)
            return None
        if self.worker is not None and self.worker.isRunning():
            self.failed.emit("Já existe um download em andamento.")
            return None

        self.worker = DownloadWorker(
            url=url,
            output_directory=output_directory,
            audio_format=audio_format,
            quality=quality,
            parent=self,
        )
        self.worker.progress.connect(self.progress.emit)
        self.worker.succeeded.connect(self._on_succeeded)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_finished)
        self.started.emit()
        self.worker.start()
        return self.worker

    def _on_succeeded(self, result):
        self.succeeded.emit(result)

    def _on_failed(self, error):
        self.failed.emit(error)

    def _on_finished(self):
        self.finished.emit()
