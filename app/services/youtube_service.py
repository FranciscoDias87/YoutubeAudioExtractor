"""Centralized YouTube extraction service.

The service owns yt-dlp interaction so UI windows do not need to know
how downloads, conversion and progress hooks are implemented.
"""

from __future__ import annotations

import os
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

    def extract_audio(
        self,
        url: str,
        format: str = "mp3",
        quality: str = "128K",
        progress_callback: Optional[Callable[[dict], None]] = None,
    ) -> dict:
        """Extract audio from a single video or playlist.

        ``progress_callback`` receives yt-dlp progress dictionaries.
        """
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
                return self._download_playlist(
                    url, info, format, quality, progress_callback
                )

            return self._download_video(url, info, format, quality, progress_callback)
        except Exception as exc:
            return {"success": False, "error": str(exc), "message": "Erro na extração."}

    def _download_video(self, url, info, format, quality, progress_callback):
        title = info.get("title", "Unknown Video")
        author = info.get("uploader", "Unknown")
        final_filename = self.file_manager.generate_filename(title, format)
        final_path = os.path.join(self.file_manager.base_directory, final_filename)

        def hook(data):
            if progress_callback:
                progress_callback(data)

        options = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": format,
                "preferredquality": quality,
            }],
            "outtmpl": os.path.join(self.file_manager.base_directory, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "progress_hooks": [hook],
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

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

    def _download_playlist(self, url, info, format, quality, progress_callback):
        playlist_title = info.get("title", "Unknown Playlist")
        playlist_dir = self.file_manager.sanitize_filename(playlist_title)
        playlist_path = os.path.join(self.file_manager.base_directory, playlist_dir)
        self.file_manager.ensure_directory_exists(playlist_path)

        def hook(data):
            if progress_callback:
                progress_callback(data)

        options = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": format,
                "preferredquality": quality,
            }],
            "outtmpl": os.path.join(playlist_path, "%(title)s.%(ext)s"),
            "noplaylist": False,
            "progress_hooks": [hook],
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        return {
            "success": True,
            "type": "playlist",
            "playlist_title": playlist_title,
            "playlist_path": playlist_path,
            "format": format,
            "quality": quality,
            "message": "Playlist baixada com sucesso!",
        }
