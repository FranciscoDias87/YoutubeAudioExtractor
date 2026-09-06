"""PyQt5 workers for metadata inspection and background downloads."""

import threading
import time

from PyQt5.QtCore import QThread, pyqtSignal

import yt_dlp

from app.logging_config import get_logger
from app.services.youtube_service import DownloadCancelled, YouTubeService


logger = get_logger("worker")


class DownloadWorker(QThread):
    """Execute one download operation in a background QThread."""

    progress = pyqtSignal(dict)
    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, url, output_directory, audio_format="mp3", quality="128K", metadata=None, parent=None):
        super().__init__(parent)
        self.url = url
        self.output_directory = output_directory
        self.audio_format = audio_format
        self.quality = quality
        self.metadata = metadata
        self._cancel_event = threading.Event()

    def cancel(self):
        logger.info("Solicitação de cancelamento recebida")
        self._cancel_event.set()

    def is_cancel_requested(self):
        return self._cancel_event.is_set()

    def run(self):
        started_at = time.perf_counter()
        logger.info(
            "run() iniciado | formato=%s | qualidade=%s | metadata_reutilizado=%s",
            self.audio_format,
            self.quality,
            self.metadata is not None,
        )
        logger.debug("URL=%s", self.url)
        try:
            service = YouTubeService(self.output_directory)
            result = service.extract_audio(
                url=self.url,
                format=self.audio_format,
                quality=self.quality,
                progress_callback=self.progress.emit,
                cancellation_callback=self.is_cancel_requested,
                metadata=self.metadata,
            )
            logger.info(
                "extract_audio() retornou após %.2fs | result=%s | cancelled=%s",
                time.perf_counter() - started_at,
                result.get("success"),
                result.get("cancelled", False),
            )
            if result.get("cancelled"):
                self.cancelled.emit()
            elif result.get("success"):
                self.succeeded.emit(result)
            else:
                self.failed.emit(result.get("error", "Erro desconhecido durante o download."))
        except DownloadCancelled:
            logger.info("DownloadCancelled após %.2fs", time.perf_counter() - started_at)
            self.cancelled.emit()
        except Exception as exc:
            logger.exception("Exceção após %.2fs: %s", time.perf_counter() - started_at, exc)
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
        started_at = time.perf_counter()
        logger.info("MetadataWorker iniciado | single=%s", self.single)
        try:
            options = {
                "quiet": True,
                "noplaylist": self.single,
                "extract_flat": not self.single,
                "skip_download": True,
            }
            logger.debug("MetadataWorker: criando YoutubeDL")
            with yt_dlp.YoutubeDL(options) as ydl:
                logger.debug("MetadataWorker: extract_info() iniciado")
                info = ydl.extract_info(self.url, download=False)
                logger.info("MetadataWorker: extract_info() concluído em %.2fs", time.perf_counter() - started_at)
            self.succeeded.emit(info)
        except Exception as exc:
            logger.exception("MetadataWorker: exceção após %.2fs: %s", time.perf_counter() - started_at, exc)
            self.failed.emit(str(exc))
