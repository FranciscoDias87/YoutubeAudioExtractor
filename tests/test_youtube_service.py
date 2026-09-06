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


def test_ffmpeg_aac_uses_utf8_with_replacement_on_windows():
    with patch("app.services.youtube_service.subprocess.run") as run:
        YouTubeService._ffmpeg_aac("input.m4a", "output.aac", "128K")

    run.assert_called_once()
    command = run.call_args.args[0]
    kwargs = run.call_args.kwargs
    assert command[:2] == ["ffmpeg", "-y"]
    assert "-c:a" in command
    assert command[command.index("-c:a") + 1] == "aac"
    assert "-f" in command
    assert command[command.index("-f") + 1] == "adts"
    assert kwargs == {"check": True, "capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}


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


def test_download_video_uses_isolated_directory_instead_of_scanning_base(tmp_path):
    service = YouTubeService(str(tmp_path))
    temp_dir = tmp_path / ".yte-video-test"
    temp_dir.mkdir()
    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value = fake_ydl
    fake_ydl.__exit__.return_value = False

    def fake_download(_urls):
        (temp_dir / "Artist - Song.mp3").write_bytes(b"audio")

    fake_ydl.download.side_effect = fake_download
    info = {"title": "Artist - Song", "uploader": "Artist"}

    with patch.object(service.file_manager, "create_temp_directory", return_value=str(temp_dir)):
        with patch("app.services.youtube_service.yt_dlp.YoutubeDL", return_value=fake_ydl):
            with patch.object(service.file_manager, "list_files", wraps=service.file_manager.list_files) as list_files:
                result = service._download_video("https://www.youtube.com/watch?v=test", info, "mp3", "128K", None)

    assert result["success"] is True
    assert os.path.exists(result["full_path"])
    assert result["filename"] == "Artist - Song.mp3"
    list_files.assert_called_once()
    assert os.path.normcase(list_files.call_args.args[0]) == os.path.normcase(str(temp_dir))
    assert not temp_dir.exists()
