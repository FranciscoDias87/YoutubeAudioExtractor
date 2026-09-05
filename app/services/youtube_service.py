"""Centralized YouTube extraction service.

The service owns yt-dlp interaction so UI windows do not need to know
how downloads, conversion and progress hooks are implemented.
"""

from __future__ import annotations

import os
import subprocess
from typing import Callable, Optional

import yt_dlp

from file_manager import FileManager


class YouTubeService:
    """Service responsible for extracting audio from YouTube URLs."""

    SUPPORTED_FORMATS = {"mp3", "aac", "wav", "flac", "m4a"}
    SUPPORTED_QUALITIES = {"64", "128", "192", "320", "64K", "128K", "192K", "320K"}

    def __init__(self, output_directory: Optional[str] = None):
        self.file_manager = FileManager(output_directory)

    @staticmethod
    def _normalize_quality(quality: str) -> str:
        value = str(quality).strip().upper()
        return value if value.endswith("K") else f"{value}K"

    @staticmethod
    def _percent(data: dict) -> int:
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes", 0)
        if not total:
            return 0
        return max(0, min(100, int(downloaded / total * 100)))

    @staticmethod
    def _postprocessor_options(audio_format: str, quality: str) -> dict:
        """Build the yt-dlp FFmpeg extraction postprocessor options."""
        # AAC is handled by a deterministic FFmpeg pass after yt-dlp.
        # Asking yt-dlp for M4A here gives us a stable intermediate container.
        codec = "m4a" if audio_format == "aac" else audio_format
        return {
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,
            "preferredquality": quality,
        }

    @staticmethod
    def _postprocessor_args(audio_format: str) -> dict:
        """Return yt-dlp postprocessor arguments for special containers."""
        return {}

    @staticmethod
    def _ffmpeg_aac(input_path: str, output_path: str, quality: str) -> None:
        """Convert an intermediate audio file to a real AAC/ADTS file."""
        bitrate = YouTubeService._normalize_quality(quality).lower()
        command = [
            "ffmpeg",
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
        subprocess.run(command, check=True, capture_output=True, text=True)

    def extract_audio(
        self,
        url: str,
        format: str = "mp3",
        quality: str = "128K",
        progress_callback: Optional[Callable[[dict], None]] = None,
    ) -> dict:
        """Extract audio from a single video or playlist."""
        url = (url or "").strip()
        format = (format or "mp3").lower().strip()

        if not url:
            return {"success": False, "error": "URL não informada."}
        if format not in self.SUPPORTED_FORMATS:
            return {"success": False, "error": f"Formato não suportado: {format}"}

        quality = self._normalize_quality(quality)
        if quality not in {"64K", "128K", "192K", "320K"}:
            return {"success": False, "error": f"Qualidade não suportada: {quality}"}

        try:
            with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": False}) as ydl:
                info = ydl.extract_info(url, download=False)

            is_playlist = info.get("_type") == "playlist"
            if is_playlist:
                return self._download_playlist(url, info, format, quality, progress_callback)

            return self._download_video(url, info, format, quality, progress_callback)
        except Exception as exc:
            return {"success": False, "error": str(exc), "message": "Erro na extração."}

    def _build_options(self, output_template, format, quality, noplaylist, progress_hook):
        options = {
            "format": "bestaudio/best",
            "postprocessors": [self._postprocessor_options(format, quality)],
            "outtmpl": output_template,
            "noplaylist": noplaylist,
            "progress_hooks": [progress_hook],
        }
        options.update(self._postprocessor_args(format))
        return options

    def _download_video(self, url, info, format, quality, progress_callback):
        title = info.get("title", "Unknown Video")
        author = info.get("uploader", "Unknown")
        final_filename = self.file_manager.generate_filename(title, format)
        final_path = os.path.join(self.file_manager.base_directory, final_filename)

        def hook(data):
            if progress_callback:
                progress_callback(data)

        options = self._build_options(
            os.path.join(self.file_manager.base_directory, "%(title)s.%(ext)s"),
            format,
            quality,
            True,
            hook,
        )

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        if format == "aac":
            intermediate = self._find_downloaded_file(title, {".m4a", ".webm", ".opus", ".mp3", ".wav", ".flac"})
            if not intermediate:
                raise FileNotFoundError("Arquivo intermediário de áudio não encontrado para conversão AAC.")
            self._ffmpeg_aac(intermediate, final_path, quality)
            if os.path.abspath(intermediate) != os.path.abspath(final_path):
                os.remove(intermediate)
        else:
            candidates = [
                os.path.join(self.file_manager.base_directory, name)
                for name in os.listdir(self.file_manager.base_directory)
                if name.startswith(title) and name.lower().endswith(f".{format}")
            ]
            if candidates:
                source = candidates[0]
                if os.path.abspath(source) != os.path.abspath(final_path):
                    renamed = self.file_manager.rename_file(source, title, format)
                    if renamed:
                        final_path = renamed
                        final_filename = os.path.basename(renamed)

        artist, song = self.file_manager.extract_artist_and_song(title)
        return {
            "success": True,
            "type": "video",
            "video_title": title,
            "video_author": author,
            "artist": artist,
            "song": song,
            "filename": final_filename,
            "full_path": final_path,
            "format": format,
            "quality": quality,
            "message": "Áudio extraído com sucesso!",
        }

    def _find_downloaded_file(self, title: str, extensions: set[str]) -> Optional[str]:
        matches = []
        for name in os.listdir(self.file_manager.base_directory):
            path = os.path.join(self.file_manager.base_directory, name)
            if os.path.isfile(path) and name.startswith(title) and os.path.splitext(name)[1].lower() in extensions:
                matches.append(path)
        return matches[0] if matches else None

    def _download_playlist(self, url, info, format, quality, progress_callback):
        playlist_title = info.get("title", "Unknown Playlist")
        playlist_dir = self.file_manager.sanitize_filename(playlist_title)
        playlist_path = os.path.join(self.file_manager.base_directory, playlist_dir)
        self.file_manager.ensure_directory_exists(playlist_path)

        def hook(data):
            if progress_callback:
                progress_callback(data)

        options = self._build_options(
            os.path.join(playlist_path, "%(title)s.%(ext)s"),
            format,
            quality,
            False,
            hook,
        )

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        if format == "aac":
            for name in os.listdir(playlist_path):
                source = os.path.join(playlist_path, name)
                if not os.path.isfile(source) or os.path.splitext(name)[1].lower() not in {".m4a", ".webm", ".opus", ".mp3", ".wav", ".flac"}:
                    continue
                output = os.path.splitext(source)[0] + ".aac"
                self._ffmpeg_aac(source, output, quality)
                os.remove(source)

        return {
            "success": True,
            "type": "playlist",
            "playlist_title": playlist_title,
            "playlist_path": playlist_path,
            "format": format,
            "quality": quality,
            "message": "Playlist baixada com sucesso!",
        }
