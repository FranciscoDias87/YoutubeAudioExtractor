"""Controller that coordinates UI requests and background workers."""

from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal

from app.services.youtube_service import YouTubeService
from app.workers.download_worker import DownloadWorker, MetadataWorker


def _trace(message):
    """Print timestamped diagnostic information to the VS Code terminal."""
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [CONTROLLER] {message}", flush=True)


class DownloadController(QObject):
    """Application-facing API for metadata inspection and audio downloads."""

    progress = pyqtSignal(dict)
    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()
    metadata_succeeded = pyqtSignal(dict)
    metadata_failed = pyqtSignal(str)
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.metadata_worker = None

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
        """Backward-compatible synchronous metadata inspection."""
        url = (url or "").strip()
        if not url:
            raise ValueError("URL não informada.")
        import yt_dlp
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": not single, "extract_flat": not single, "skip_download": True}) as ydl:
            return ydl.extract_info(url, download=False)

    def inspect_async(self, url, single=False):
        """Inspect metadata without blocking the Qt main thread."""
        url = (url or "").strip()
        if not url:
            self.metadata_failed.emit("URL não informada.")
            return None
        if self.metadata_worker is not None and self.metadata_worker.isRunning():
            self.metadata_failed.emit("Já existe um processamento de URL em andamento.")
            return None
        self.metadata_worker = MetadataWorker(url, single=single, parent=self)
        self.metadata_worker.succeeded.connect(self.metadata_succeeded.emit)
        self.metadata_worker.failed.connect(self.metadata_failed.emit)
        self.metadata_worker.start()
        return self.metadata_worker

    def download(self, url, output_directory, audio_format="mp3", quality="128K"):
        """Start a background download and return the worker."""
        _trace("download() chamado")
        valid, error = self.validate(url, audio_format, quality)
        if not valid:
            _trace(f"Validação falhou: {error}")
            self.failed.emit(error)
            return None
        if self.worker is not None and self.worker.isRunning():
            _trace("Download rejeitado: já existe um worker em andamento")
            self.failed.emit("Já existe um download em andamento.")
            return None
        _trace("Criando DownloadWorker...")
        self.worker = DownloadWorker(url=url, output_directory=output_directory, audio_format=audio_format, quality=quality, parent=self)
        self.worker.progress.connect(self.progress.emit)
        self.worker.succeeded.connect(self._on_succeeded)
        self.worker.failed.connect(self._on_failed)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.finished.connect(self._on_finished)
        _trace("DownloadWorker criado; emitindo started")
        self.started.emit()
        _trace("Iniciando DownloadWorker.start()")
        self.worker.start()
        _trace("DownloadWorker.start() retornou")
        return self.worker

    def cancel(self):
        """Request cancellation of the active download."""
        _trace("cancel() chamado")
        if self.worker is not None and self.worker.isRunning():
            self.worker.cancel()
            return True
        _trace("Nenhum DownloadWorker ativo para cancelar")
        return False

    def _on_succeeded(self, result):
        self.succeeded.emit(result)

    def _on_failed(self, error):
        self.failed.emit(error)

    def _on_cancelled(self):
        self.cancelled.emit()

    def _on_finished(self):
        self.finished.emit()
