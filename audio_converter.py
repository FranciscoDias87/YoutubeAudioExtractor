"""Audio conversion service backed by FFmpeg.

This module is intentionally independent from YouTube/yt-dlp concerns. The
YouTube service can delegate audio transcoding here without knowing how FFmpeg
is invoked.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class AudioConversionError(RuntimeError):
    """Base exception for audio conversion failures."""


class FFmpegNotFoundError(AudioConversionError):
    """Raised when FFmpeg cannot be found in PATH."""


class AudioConverter:
    """Convert audio files using FFmpeg."""

    def __init__(self, ffmpeg_command: str = "ffmpeg") -> None:
        self.ffmpeg_command = ffmpeg_command

    @staticmethod
    def _normalize_quality(quality: str | int) -> str:
        value = str(quality).strip().upper()
        if value.endswith("K"):
            value = value[:-1]
        if not value.isdigit() or int(value) <= 0:
            raise ValueError(f"Qualidade inválida: {quality}")
        return f"{value}K"

    @staticmethod
    def _validate_paths(input_path: str, output_path: str) -> None:
        if not input_path:
            raise ValueError("Arquivo de entrada não informado.")
        if not output_path:
            raise ValueError("Arquivo de saída não informado.")
        source = Path(input_path)
        if not source.is_file():
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

    def convert_to_aac(
        self,
        input_path: str,
        output_path: str,
        quality: str | int = "128K",
    ) -> str:
        """Convert an audio file to AAC/ADTS and return the output path."""
        self._validate_paths(input_path, output_path)
        bitrate = self._normalize_quality(quality).lower()
        command = [
            self.ffmpeg_command,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            bitrate,
            "-f",
            "adts",
            output_path,
        ]
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise FFmpegNotFoundError(
                "FFmpeg não encontrado. Certifique-se de que está instalado e no PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            detail = f" FFmpeg: {stderr}" if stderr else ""
            raise AudioConversionError(
                f"Falha ao converter áudio para AAC.{detail}"
            ) from exc
        return os.fspath(output_path)


def convert_audio(input_path, output_path, output_format, quality_kbps):
    """Backward-compatible wrapper retained during the staged refactor."""
    output_format = str(output_format).strip().lower()
    if output_format != "aac":
        raise ValueError(
            "O AudioConverter modernizado suporta AAC nesta etapa; "
            f"formato recebido: {output_format}"
        )
    return AudioConverter().convert_to_aac(input_path, output_path, quality_kbps)
