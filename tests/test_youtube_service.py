import os

from app.services.youtube_service import YouTubeService
from file_manager import FileManager


def test_normalize_quality_adds_k_suffix():
    assert YouTubeService._normalize_quality("128") == "128K"
    assert YouTubeService._normalize_quality("320K") == "320K"


def test_aac_uses_adts_and_aac_codec():
    options = YouTubeService._postprocessor_options("aac", "128K")
    args = YouTubeService._postprocessor_args("aac")

    assert options["preferredcodec"] == "aac"
    assert args["ExtractAudio"] == ["-c:a", "aac", "-f", "adts"]


def test_m4a_does_not_use_aac_adts_override():
    options = YouTubeService._postprocessor_options("m4a", "128K")
    args = YouTubeService._postprocessor_args("m4a")

    assert options["preferredcodec"] == "m4a"
    assert args == {}


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


def test_default_output_directory_is_audio():
    file_manager = FileManager()

    assert os.path.basename(file_manager.base_directory) == "Audio"
    assert os.path.basename(file_manager.base_directory) != "Audios"


def test_legacy_audios_directory_is_redirected_to_audio():
    legacy_directory = os.path.join(os.path.expanduser("~"), "Audios")
    file_manager = FileManager(legacy_directory)

    assert os.path.basename(file_manager.base_directory) == "Audio"
