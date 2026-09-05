from unittest.mock import patch

from app.controllers.download_controller import DownloadController
from app.workers.download_worker import DownloadWorker


def test_controller_accepts_supported_download_parameters():
    valid, error = DownloadController.validate(
        "https://www.youtube.com/watch?v=test",
        "mp3",
        "128",
    )
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


def test_worker_emits_success_for_service_result(qtbot):
    result = {
        "success": True,
        "type": "video",
        "filename": "teste.mp3",
        "message": "Áudio extraído com sucesso!",
    }
    with patch("app.workers.download_worker.YouTubeService") as service_cls:
        service_cls.return_value.extract_audio.return_value = result
        worker = DownloadWorker("https://youtu.be/test", ".", "mp3", "128K")
        received = []
        worker.succeeded.connect(received.append)
        worker.run()
        assert received == [result]


def test_worker_emits_error_for_service_failure(qtbot):
    with patch("app.workers.download_worker.YouTubeService") as service_cls:
        service_cls.return_value.extract_audio.return_value = {
            "success": False,
            "error": "falha simulada",
        }
        worker = DownloadWorker("https://youtu.be/test", ".", "mp3", "128K")
        errors = []
        worker.failed.connect(errors.append)
        worker.run()
        assert errors == ["falha simulada"]
