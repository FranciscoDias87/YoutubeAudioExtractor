from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.ffmpeg_manager import (
    FFmpegManager,
    FFmpegNotFoundError,
    FFmpegValidationError,
)


def test_locate_prefers_explicit_executable(tmp_path):
    explicit = tmp_path / "custom-ffmpeg.exe"
    explicit.write_bytes(b"ffmpeg")
    manager = FFmpegManager(executable=str(explicit), application_root=str(tmp_path))

    assert manager.locate() == str(explicit.resolve())


def test_locate_prefers_bundled_ffmpeg_over_system(tmp_path):
    bundled = tmp_path / "ffmpeg" / "ffmpeg.exe"
    bundled.parent.mkdir()
    bundled.write_bytes(b"ffmpeg")
    manager = FFmpegManager(application_root=str(tmp_path))

    with patch("app.services.ffmpeg_manager.shutil.which", return_value="C:/Windows/ffmpeg.exe"):
        assert manager.locate() == str(bundled.resolve())


def test_default_application_root_uses_pyinstaller_meipass():
    with patch("app.services.ffmpeg_manager.sys.frozen", True, create=True), patch(
        "app.services.ffmpeg_manager.sys._MEIPASS", r"C:\\Temp\\_MEI12345", create=True
    ):
        assert FFmpegManager._default_application_root() == Path(r"C:\\Temp\\_MEI12345")


def test_locate_falls_back_to_system_path(tmp_path):
    manager = FFmpegManager(application_root=str(tmp_path))

    with patch("app.services.ffmpeg_manager.shutil.which", return_value="C:/Tools/ffmpeg.exe"):
        assert manager.locate() == str(Path("C:/Tools/ffmpeg.exe").resolve())


def test_locate_returns_none_when_ffmpeg_is_unavailable(tmp_path):
    manager = FFmpegManager(application_root=str(tmp_path))

    with patch("app.services.ffmpeg_manager.shutil.which", return_value=None):
        assert manager.locate() is None


def test_validate_accepts_working_ffmpeg(tmp_path):
    executable = tmp_path / "ffmpeg.exe"
    executable.write_bytes(b"ffmpeg")

    with patch("app.services.ffmpeg_manager.subprocess.run") as run:
        run.return_value.stdout = "ffmpeg version 8.0"
        assert FFmpegManager.validate(str(executable)) == str(executable.resolve())

    kwargs = run.call_args.kwargs
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"
    assert kwargs["timeout"] == 10


def test_validate_rejects_missing_executable(tmp_path):
    with pytest.raises(FFmpegNotFoundError):
        FFmpegManager.validate(str(tmp_path / "missing.exe"))


def test_validate_maps_timeout(tmp_path):
    executable = tmp_path / "ffmpeg.exe"
    executable.write_bytes(b"ffmpeg")

    with patch(
        "app.services.ffmpeg_manager.subprocess.run",
        side_effect=__import__("subprocess").TimeoutExpired("ffmpeg", 10),
    ):
        with pytest.raises(FFmpegValidationError, match="não respondeu"):
            FFmpegManager.validate(str(executable))


def test_resolve_raises_when_no_ffmpeg_is_found(tmp_path):
    manager = FFmpegManager(application_root=str(tmp_path))
    with patch("app.services.ffmpeg_manager.shutil.which", return_value=None):
        with pytest.raises(FFmpegNotFoundError, match="FFmpeg não encontrado"):
            manager.resolve()
