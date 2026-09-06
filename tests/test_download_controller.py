from unittest.mock import patch

from app.controllers.download_controller import DownloadController
from app.workers.download_worker import DownloadWorker


def test_controller_accepts_supported_download_parameters():
    valid, error = DownloadController.validate("https://www.youtube.com/watch?v=test", "mp3", "128")
    assert valid is True
    assert error == ""


def test_controller_rejects_invalid_youtube_url():
    valid, error = DownloadController.validate("https://example.com/video", "mp3", "128")
    assert valid is False
    assert "YouTube" in error


def test_controller_rejects_invalid_format():
    valid, error = DownloadController.validate("https://youtu.be/test", "ogg", "128")
    assert valid is False
    assert "Formato" in error


def test_controller_rejects_invalid_quality():
    valid, error = DownloadController.validate("https://youtu.be/test", "mp3", "999")
    assert valid is False
    assert "Qualidade" in error


def test_worker_emits_success_for_service_result():
    result = {"success": True, "type": "video", "filename": "teste.mp3", "message": "Áudio extraído com sucesso!"}
    with patch("app.workers.download_worker.YouTubeService") as service_cls:
        service_cls.return_value.extract_audio.return_value = result
        worker = DownloadWorker("https://youtu.be/test", ".", "mp3", "128K")
        received = []
        worker.succeeded.connect(received.append)
        worker.run()
        assert received == [result]
        service_cls.return_value.extract_audio.assert_called_once()


def test_worker_passes_reused_metadata_to_service():
    metadata = {"_type": "playlist", "title": "Playlist", "entries": []}
    with patch("app.workers.download_worker.YouTubeService") as service_cls:
        service_cls.return_value.extract_audio.return_value = {"success": False, "error": "simulada"}
        worker = DownloadWorker("https://youtu.be/test", ".", "mp3", "128K", metadata=metadata)
        worker.run()
        kwargs = service_cls.return_value.extract_audio.call_args.kwargs
        assert kwargs["metadata"] is metadata


def test_worker_emits_error_for_service_failure():
    with patch("app.workers.download_worker.YouTubeService") as service_cls:
        service_cls.return_value.extract_audio.return_value = {"success": False, "error": "falha simulada"}
        worker = DownloadWorker("https://youtu.be/test", ".", "mp3", "128K")
        errors = []
        worker.failed.connect(errors.append)
        worker.run()
        assert errors == ["falha simulada"]


def test_worker_cancel_sets_cancellation_flag():
    worker = DownloadWorker("https://youtu.be/test", ".", "mp3", "128K")
    assert worker.is_cancel_requested() is False
    worker.cancel()
    assert worker.is_cancel_requested() is True


def test_controller_cancel_returns_false_without_active_worker():
    controller = DownloadController()
    assert controller.cancel() is False
