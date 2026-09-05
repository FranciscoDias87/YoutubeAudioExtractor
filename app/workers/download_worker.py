"""PyQt5 workers for metadata inspection and background downloads."""

import threading
import time
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal

import yt_dlp

from app.services.youtube_service import DownloadCancelled, YouTubeService


def _trace(message):
    """Print timestamped diagnostic information to the VS Code terminal."""
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [WORKER] {message}", flush=True)


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
        _trace("Solicitação de cancelamento recebida")
        self._cancel_event.set()

    def is_cancel_requested(self):
        return self._cancel_event.is_set()

    def run(self):
        started_at = time.perf_counter()
        _trace(f"run() iniciado | formato={self.audio_format} | qualidade={self.quality}")
        _trace(f"URL={self.url}")
        try:
            _trace("Criando YouTubeService...")
            service = YouTubeService(self.output_directory)
            _trace("YouTubeService criado")
            _trace("Chamando YouTubeService.extract_audio()...")
            result = service.extract_audio(
                url=self.url,
                format=self.audio_format,
                quality=self.quality,
                progress_callback=self.progress.emit,
                cancellation_callback=self.is_cancel_requested,
            )
            _trace(f"extract_audio() retornou após {time.perf_counter() - started_at:.2f}s | result={result.get('success')} | cancelled={result.get('cancelled', False)}")
            if result.get("cancelled"):
                self.cancelled.emit()
            elif result.get("success"):
                self.succeeded.emit(result)
            else:
                self.failed.emit(result.get("error", "Erro desconhecido durante o download."))
        except DownloadCancelled:
            _trace(f"DownloadCancelled após {time.perf_counter() - started_at:.2f}s")
            self.cancelled.emit()
        except Exception as exc:
            _trace(f"EXCEÇÃO após {time.perf_counter() - started_at:.2f}s: {exc}")
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
        _trace(f"MetadataWorker iniciado | single={self.single}")
        try:
            options = {
                "quiet": True,
                "noplaylist": self.single,
                "extract_flat": not self.single,
                "skip_download": True,
            }
            _trace("MetadataWorker: criando YoutubeDL")
            with yt_dlp.YoutubeDL(options) as ydl:
                _trace("MetadataWorker: extract_info() iniciado")
                info = ydl.extract_info(self.url, download=False)
                _trace(f"MetadataWorker: extract_info() concluído em {time.perf_counter() - started_at:.2f}s")
            self.succeeded.emit(info)
        except Exception as exc:
            _trace(f"MetadataWorker: EXCEÇÃO após {time.perf_counter() - started_at:.2f}s: {exc}")
            self.failed.emit(str(exc))
