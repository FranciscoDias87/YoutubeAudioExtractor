from pathlib import Path
from unittest.mock import patch
import subprocess

import pytest

from audio_converter import AudioConversionError, AudioConverter, FFmpegNotFoundError


@patch("audio_converter.FFmpegManager.resolve", return_value="ffmpeg")
def test_convert_to_aac_builds_expected_ffmpeg_command(_resolve, tmp_path):
    source = tmp_path / "input.m4a"
    output = tmp_path / "output.aac"
    source.write_bytes(b"audio")

    with patch("audio_converter.subprocess.run") as run:
        result = AudioConverter().convert_to_aac(str(source), str(output), "128K")

    assert result == str(output)
    command = run.call_args.args[0]
    assert command == [
        "ffmpeg", "-y", "-i", str(source), "-vn",
        "-c:a", "aac", "-b:a", "128k", "-f", "adts", str(output)
    ]
    kwargs = run.call_args.kwargs
    assert kwargs["check"] is True
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"
    if __import__("os").name == "nt":
        assert kwargs["creationflags"] == subprocess.CREATE_NO_WINDOW
        startupinfo = kwargs["startupinfo"]
        assert startupinfo is not None
        assert startupinfo.dwFlags & subprocess.STARTF_USESHOWWINDOW
        assert startupinfo.wShowWindow == subprocess.SW_HIDE
    else:
        assert kwargs["creationflags"] == 0
        assert kwargs["startupinfo"] is None


@patch("audio_converter.FFmpegManager.resolve", return_value="ffmpeg")
def test_convert_to_aac_accepts_numeric_quality(_resolve, tmp_path):
    source = tmp_path / "input.m4a"
    output = tmp_path / "nested" / "output.aac"
    source.write_bytes(b"audio")

    with patch("audio_converter.subprocess.run") as run:
        AudioConverter().convert_to_aac(str(source), str(output), 192)

    command = run.call_args.args[0]
    assert command[command.index("-b:a") + 1] == "192k"
    assert output.parent.is_dir()


@patch("audio_converter.FFmpegManager.resolve", return_value="ffmpeg")
def test_convert_to_aac_rejects_missing_input(_resolve, tmp_path):
    with pytest.raises(FileNotFoundError):
        AudioConverter().convert_to_aac(
            str(tmp_path / "missing.m4a"), str(tmp_path / "output.aac"), "128K"
        )


@patch("audio_converter.FFmpegManager.resolve", return_value="ffmpeg")
def test_convert_to_aac_rejects_invalid_quality(_resolve, tmp_path):
    source = tmp_path / "input.m4a"
    source.write_bytes(b"audio")

    with pytest.raises(ValueError, match="Qualidade inválida"):
        AudioConverter().convert_to_aac(str(source), str(tmp_path / "output.aac"), "abc")


@patch("audio_converter.FFmpegManager.resolve", return_value="ffmpeg")
def test_convert_to_aac_maps_missing_ffmpeg(_resolve, tmp_path):
    source = tmp_path / "input.m4a"
    source.write_bytes(b"audio")

    with patch("audio_converter.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(FFmpegNotFoundError, match="FFmpeg não encontrado"):
            AudioConverter().convert_to_aac(str(source), str(tmp_path / "output.aac"))


@patch("audio_converter.FFmpegManager.resolve", return_value="ffmpeg")
def test_convert_to_aac_maps_ffmpeg_failure(_resolve, tmp_path):
    source = tmp_path / "input.m4a"
    source.write_bytes(b"audio")
    error = subprocess.CalledProcessError(1, ["ffmpeg"], stderr="falha")

    with patch("audio_converter.subprocess.run", side_effect=error):
        with pytest.raises(AudioConversionError, match="Falha ao converter áudio"):
            AudioConverter().convert_to_aac(str(source), str(tmp_path / "output.aac"))


def test_legacy_convert_audio_delegates_aac(tmp_path):
    source = tmp_path / "input.m4a"
    output = tmp_path / "output.aac"
    source.write_bytes(b"audio")

    with patch.object(AudioConverter, "convert_to_aac", return_value=str(output)) as convert:
        with patch("audio_converter.FFmpegManager.resolve", return_value="ffmpeg"):
            result = __import__("audio_converter").convert_audio(
                str(source), str(output), "aac", 128
            )

    assert result == str(output)
    convert.assert_called_once_with(str(source), str(output), 128)
