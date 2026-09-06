"""FFmpeg discovery and validation for YouTube Audio Extractor."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


class FFmpegDependencyError(RuntimeError):
    """Base exception for FFmpeg dependency problems."""


class FFmpegNotFoundError(FFmpegDependencyError):
    """Raised when no usable FFmpeg executable can be found."""


class FFmpegValidationError(FFmpegDependencyError):
    """Raised when a discovered FFmpeg executable cannot be validated."""


class FFmpegManager:
    """Locate and validate the FFmpeg executable used by the application.

    Resolution order is deterministic: explicit path, bundled application copy,
    then the system PATH. The manager never modifies the user's PATH.
    """

    EXECUTABLE_NAME = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"

    def __init__(self, executable: Optional[str] = None, application_root: Optional[str] = None) -> None:
        self.executable = executable
        self.application_root = Path(application_root) if application_root else self._default_application_root()

    @staticmethod
    def _default_application_root() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[2]

    def bundled_candidates(self) -> list[Path]:
        return [
            self.application_root / "ffmpeg" / self.EXECUTABLE_NAME,
            self.application_root / "bin" / self.EXECUTABLE_NAME,
            self.application_root / self.EXECUTABLE_NAME,
        ]

    def locate(self) -> Optional[str]:
        if self.executable:
            explicit = Path(self.executable)
            return str(explicit.resolve()) if explicit.is_file() else None

        for candidate in self.bundled_candidates():
            if candidate.is_file():
                return str(candidate.resolve())

        system_path = shutil.which("ffmpeg")
        return str(Path(system_path).resolve()) if system_path else None

    @staticmethod
    def validate(executable: str) -> str:
        if not executable:
            raise FFmpegNotFoundError("FFmpeg não foi localizado.")

        path = Path(executable)
        if not path.is_file():
            raise FFmpegNotFoundError(f"Executável FFmpeg não encontrado: {executable}")

        try:
            result = subprocess.run(
                [str(path), "-version"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        except FileNotFoundError as exc:
            raise FFmpegNotFoundError(f"Executável FFmpeg não encontrado: {executable}") from exc
        except subprocess.TimeoutExpired as exc:
            raise FFmpegValidationError("FFmpeg não respondeu dentro do tempo esperado.") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            raise FFmpegValidationError(
                f"FFmpeg encontrado, mas não pôde ser validado.{(' ' + detail) if detail else ''}"
            ) from exc
        except OSError as exc:
            raise FFmpegValidationError(f"Não foi possível executar o FFmpeg: {exc}") from exc

        if not (result.stdout or "").strip():
            raise FFmpegValidationError("FFmpeg respondeu sem informar a versão.")

        return str(path.resolve())

    def resolve(self) -> str:
        located = self.locate()
        if not located:
            raise FFmpegNotFoundError(
                "FFmpeg não encontrado. A instalação do YouTube Audio Extractor "
                "deve disponibilizar uma cópia compatível do FFmpeg."
            )
        return self.validate(located)
