"""Prepare the pinned FFmpeg Windows dependency for packaging.

The script downloads a pinned LGPL static build, verifies its SHA-256 digest,
extracts ffmpeg.exe/ffprobe.exe and validates ffmpeg.exe before PyInstaller.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ffmpeg"
VERSION = "n9.0-latest-win64-lgpl-9.0"
URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
    f"latest/ffmpeg-{VERSION}.zip"
)
# The checksum is intentionally required to be supplied from the pinned
# release checksums file before a release build. Do not weaken this check.
EXPECTED_SHA256 = os.environ.get("YOUTUBE_AUDIO_EXTRACTOR_FFMPEG_SHA256", "").strip().lower()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(path: Path) -> str:
    result = subprocess.run(
        [str(path), "-version"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    first_line = (result.stdout or "").splitlines()[0].strip()
    if not first_line:
        raise RuntimeError("FFmpeg foi executado, mas não informou a versão.")
    return first_line


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("A preparação atual do FFmpeg é destinada ao Windows x64.")
    if not EXPECTED_SHA256:
        raise SystemExit(
            "Defina YOUTUBE_AUDIO_EXTRACTOR_FFMPEG_SHA256 com o SHA-256 do "
            "artefato FFmpeg pinado antes de executar o build."
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="yte-ffmpeg-") as temp_dir:
        temp = Path(temp_dir)
        archive = temp / "ffmpeg.zip"
        print(f"Baixando FFmpeg: {URL}")
        urllib.request.urlretrieve(URL, archive)

        actual = sha256(archive)
        if actual != EXPECTED_SHA256:
            raise SystemExit(
                f"SHA-256 inválido para FFmpeg: esperado={EXPECTED_SHA256} recebido={actual}"
            )

        extract = temp / "extract"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract)

        candidates = list(extract.rglob("ffmpeg.exe"))
        if not candidates:
            raise SystemExit("O pacote FFmpeg não contém ffmpeg.exe.")
        ffmpeg = candidates[0]
        ffprobe_candidates = list(extract.rglob("ffprobe.exe"))

        for filename in ("ffmpeg.exe", "ffprobe.exe", "LICENSE.txt"):
            target = OUTPUT / filename
            if target.exists():
                target.unlink()

        shutil.copy2(ffmpeg, OUTPUT / "ffmpeg.exe")
        if ffprobe_candidates:
            shutil.copy2(ffprobe_candidates[0], OUTPUT / "ffprobe.exe")

        license_candidates = list(extract.rglob("LICENSE.txt"))
        if license_candidates:
            shutil.copy2(license_candidates[0], OUTPUT / "LICENSE.txt")

    version = validate(OUTPUT / "ffmpeg.exe")
    manifest = {
        "source": "BtbN/FFmpeg-Builds",
        "version": VERSION,
        "url": URL,
        "archive_sha256": EXPECTED_SHA256,
        "ffmpeg_version": version,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"FFmpeg preparado e validado: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
