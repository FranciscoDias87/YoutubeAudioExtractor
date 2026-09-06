"""Prepare the pinned FFmpeg Windows dependency for packaging.

The build uses a reproducible LGPL static FFmpeg artifact. The archive is
verified by SHA-256 before extraction and ffmpeg.exe is validated before
PyInstaller packages the application.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ffmpeg"
RELEASE_TAG = "autobuild-2026-08-29-13-12"
ARCHIVE_NAME = "ffmpeg-n9.0.1-11-ge47273f4d9-win64-lgpl-9.0.zip"
URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
    f"{RELEASE_TAG}/{ARCHIVE_NAME}"
)
EXPECTED_SHA256 = "f43aaeb86d05b453f3909d0d1eed39a51db71d387c21a3605676c1d1627084d9"


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

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="yte-ffmpeg-") as temp_dir:
        temp = Path(temp_dir)
        archive = temp / ARCHIVE_NAME
        print(f"Baixando FFmpeg pinado: {URL}")
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
        license_candidates = list(extract.rglob("LICENSE.txt"))

        for filename in ("ffmpeg.exe", "ffprobe.exe", "LICENSE.txt"):
            target = OUTPUT / filename
            if target.exists():
                target.unlink()

        shutil.copy2(ffmpeg, OUTPUT / "ffmpeg.exe")
        if ffprobe_candidates:
            shutil.copy2(ffprobe_candidates[0], OUTPUT / "ffprobe.exe")
        if license_candidates:
            shutil.copy2(license_candidates[0], OUTPUT / "LICENSE.txt")

    version = validate(OUTPUT / "ffmpeg.exe")
    manifest = {
        "source": "BtbN/FFmpeg-Builds",
        "release_tag": RELEASE_TAG,
        "archive": ARCHIVE_NAME,
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
