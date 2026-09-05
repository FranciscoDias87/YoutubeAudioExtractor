from app.services.youtube_service import YouTubeService


def test_normalize_quality_adds_k_suffix():
    assert YouTubeService._normalize_quality("128") == "128K"
    assert YouTubeService._normalize_quality("320K") == "320K"


def test_invalid_url_is_rejected(tmp_path):
    service = YouTubeService(str(tmp_path))
    result = service.extract_audio("")

    assert result["success"] is False
    assert "URL" in result["error"]


def test_invalid_format_is_rejected(tmp_path):
    service = YouTubeService(str(tmp_path))
    result = service.extract_audio("https://www.youtube.com/watch?v=test", format="ogg")

    assert result["success"] is False
    assert "Formato" in result["error"]
