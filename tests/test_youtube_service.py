import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.youtube_service import DownloadCancelled, YouTubeService
from file_manager import FileManager


def test_normalize_quality_adds_k_suffix():
    assert YouTubeService._normalize_quality("128") == "128K"
    assert YouTubeService._normalize_quality("320K") == "320K"


def test_aac_uses_m4a_as_intermediate_for_ffmpeg():
    options = YouTubeService._postprocessor_options("aac", "128K")
    assert options["preferredcodec"] == "m4a"
    assert options["preferredquality"] == "128K"


def test_non_aac_keeps_requested_codec():
    options = YouTubeService._postprocessor_options("mp3", "128K")
    assert options["preferredcodec"] == "mp3"


def test_aac_has_no_yt_dlp_container_override():
    assert YouTubeService._postprocessor_args("aac") == {}


def test_build_options_uses_named_outtmpl_for_yt_dlp_process_ie_result():
    options = YouTubeService._build_options(
        r"C:\Audio\%(title)s.%(ext)s",
        "mp3",
        "128K",
        True,
        lambda _data: None,
    )

    assert options["outtmpl"] == {"default": r"C:\Audio\%(title)s.%(ext)s"}


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


def test_cancellation_callback_raises_download_cancelled():
    with pytest.raises(DownloadCancelled):
        YouTubeService._check_cancel(lambda: True)


def test_percent_uses_downloaded_bytes():
    assert YouTubeService._percent({"downloaded_bytes": 25, "total_bytes": 100}) == 25


def test_single_video_reuses_metadata_without_second_extract_info(tmp_path):
    metadata = {"_type": "video", "id": "abc123", "title": "Vídeo de teste", "uploader": "Canal de teste"}
    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value = fake_ydl
    fake_ydl.__exit__.return_value = False

    with patch("app.services.youtube_service.yt_dlp.YoutubeDL", return_value=fake_ydl) as ydl_cls:
        with patch.object(YouTubeService, "_download_video", return_value={"success": True}) as download_video:
            service = YouTubeService(str(tmp_path))
            result = service.extract_audio("https://www.youtube.com/watch?v=abc123", format="mp3", quality="128K", metadata=metadata)

    assert result["success"] is True
    fake_ydl.extract_info.assert_not_called()
    ydl_cls.assert_not_called()
    download_video.assert_called_once()
    assert download_video.call_args.args[1] is metadata


def test_service_accepts_injected_audio_converter(tmp_path):
    converter = MagicMock()
    service = YouTubeService(str(tmp_path), audio_converter=converter)

    assert service.audio_converter is converter


def test_convert_aac_delegates_to_audio_converter(tmp_path):
    converter = MagicMock()
    converter.convert_to_aac.return_value = str(tmp_path / "output.aac")
    service = YouTubeService(str(tmp_path), audio_converter=converter)

    result = service._convert_aac(
        str(tmp_path / "input.m4a"),
        str(tmp_path / "output.aac"),
        "128K",
    )

    assert result == str(tmp_path / "output.aac")
    converter.convert_to_aac.assert_called_once_with(
        str(tmp_path / "input.m4a"),
        str(tmp_path / "output.aac"),
        "128K",
    )


def test_download_video_uses_audio_converter_for_aac(tmp_path):
    service = YouTubeService(str(tmp_path), audio_converter=MagicMock())
    temp_dir = tmp_path / ".yte-video-test"
    temp_dir.mkdir()
    source = temp_dir / "Artist - Song.m4a"
    source.write_bytes(b"audio")

    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value = fake_ydl
    fake_ydl.__exit__.return_value = False

    def fake_download(_urls):
        return None

    fake_ydl.download.side_effect = fake_download
    info = {"title": "Artist - Song", "uploader": "Artist"}
    service.audio_converter.convert_to_aac.return_value = str(tmp_path / "Artist - Song.aac")

    with patch.object(service.file_manager, "create_temp_directory", return_value=str(temp_dir)):
        with patch("app.services.youtube_service.yt_dlp.YoutubeDL", return_value=fake_ydl):
            result = service._download_video("https://www.youtube.com/watch?v=test", info, "aac", "128K", None)

    assert result["success"] is True
    service.audio_converter.convert_to_aac.assert_called_once()
    call_args = service.audio_converter.convert_to_aac.call_args.args
    assert call_args[0] == str(source)
    assert call_args[1].endswith("Artist - Song.aac")
    assert call_args[2] == "128K"
    assert not temp_dir.exists()


def test_download_video_keeps_shutil_move_for_non_aac(tmp_path):
    service = YouTubeService(str(tmp_path), audio_converter=MagicMock())
    temp_dir = tmp_path / ".yte-video-test"
    temp_dir.mkdir()
    source = temp_dir / "Artist - Song.mp3"
    source.write_bytes(b"audio")

    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value = fake_ydl
    fake_ydl.__exit__.return_value = False
    fake_ydl.download.side_effect = lambda _urls: None
    info = {"title": "Artist - Song", "uploader": "Artist"}

    with patch.object(service.file_manager, "create_temp_directory", return_value=str(temp_dir)):
        with patch("app.services.youtube_service.yt_dlp.YoutubeDL", return_value=fake_ydl):
            result = service._download_video("https://www.youtube.com/watch?v=test", info, "mp3", "128K", None)

    assert result["success"] is True
    service.audio_converter.convert_to_aac.assert_not_called()
    assert os.path.exists(result["full_path"])
    assert result["filename"] == "Artist - Song.mp3"
    assert not temp_dir.exists()
