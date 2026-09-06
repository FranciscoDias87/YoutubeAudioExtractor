"""Centralized YouTube extraction service."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from typing import Callable, Optional

import yt_dlp

from file_manager import FileManager
from app.logging_config import get_logger


logger = get_logger("service")


class DownloadCancelled(Exception):
    """Raised internally when an active download receives a cancel request."""


class YouTubeService:
    """Service responsible for extracting audio from YouTube URLs."""

    SUPPORTED_FORMATS = {"mp3", "aac", "wav", "flac", "m4a"}
    SUPPORTED_QUALITIES = {"64", "128", "192", "320", "64K", "128K", "192K", "320K"}
    INTERMEDIATE_EXTENSIONS = {".m4a", ".webm", ".opus", ".mp3", ".wav", ".flac"}

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
        codec = "m4a" if audio_format == "aac" else audio_format
        return {"key": "FFmpegExtractAudio", "preferredcodec": codec, "preferredquality": quality}

    @staticmethod
    def _postprocessor_args(audio_format: str) -> dict:
        return {}

    @staticmethod
    def _ffmpeg_aac(input_path: str, output_path: str, quality: str) -> None:
        bitrate = YouTubeService._normalize_quality(quality).lower()
        command = ["ffmpeg", "-y", "-i", input_path, "-vn", "-c:a", "aac", "-b:a", bitrate, "-f", "adts", output_path]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")

    @staticmethod
    def _check_cancel(cancellation_callback: Optional[Callable[[], bool]]) -> None:
        if cancellation_callback and cancellation_callback():
            raise DownloadCancelled()

    def extract_audio(self, url: str, format: str = "mp3", quality: str = "128K",
                      progress_callback: Optional[Callable[[dict], None]] = None,
                      cancellation_callback: Optional[Callable[[], bool]] = None,
                      metadata: Optional[dict] = None) -> dict:
        started_at = time.perf_counter()
        url = (url or "").strip()
        format = (format or "mp3").lower().strip()
        logger.info("extract_audio() iniciado | formato=%s | qualidade=%s | metadata_reutilizado=%s", format, quality, metadata is not None)
        if not url:
            return {"success": False, "error": "URL não informada."}
        if format not in self.SUPPORTED_FORMATS:
            return {"success": False, "error": f"Formato não suportado: {format}"}
        quality = self._normalize_quality(quality)
        if quality not in {"64K", "128K", "192K", "320K"}:
            return {"success": False, "error": f"Qualidade não suportada: {quality}"}

        try:
            self._check_cancel(cancellation_callback)
            if metadata is not None:
                info = metadata
                logger.info("Usando metadados fornecidos pelo MetadataWorker; extract_info() adicional será evitado.")
            else:
                info_started = time.perf_counter()
                logger.debug("Criando YoutubeDL para consulta de metadados do download...")
                with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": False}) as ydl:
                    logger.debug("extract_info() do download iniciado")
                    info = ydl.extract_info(url, download=False)
                logger.info("extract_info() do download concluído em %.2fs", time.perf_counter() - info_started)

            self._check_cancel(cancellation_callback)
            info_type = info.get("_type")
            logger.debug("Tipo retornado pelo yt-dlp: %s", info_type or "video")
            if info_type == "playlist":
                result = self._download_playlist(url, info, format, quality, progress_callback, cancellation_callback)
            else:
                result = self._download_video(url, info, format, quality, progress_callback, cancellation_callback)
            logger.info("extract_audio() concluído em %.2fs", time.perf_counter() - started_at)
            return result
        except DownloadCancelled:
            logger.info("Download cancelado após %.2fs", time.perf_counter() - started_at)
            return {"success": False, "cancelled": True, "message": "Download cancelado pelo usuário."}
        except Exception as exc:
            logger.exception("Erro após %.2fs: %s", time.perf_counter() - started_at, exc)
            return {"success": False, "error": str(exc), "message": "Erro na extração."}

    @staticmethod
    def _build_options(output_template, format, quality, noplaylist, progress_hook):
        return {
            "format": "bestaudio/best",
            "postprocessors": [YouTubeService._postprocessor_options(format, quality)],
            "outtmpl": {"default": output_template},
            "noplaylist": noplaylist,
            "progress_hooks": [progress_hook],
        } | YouTubeService._postprocessor_args(format)

    def _download_video(self, url, info, format, quality, progress_callback, cancellation_callback=None):
        started_at = time.perf_counter()
        title = info.get("title", "Unknown Video")
        author = info.get("uploader", "Unknown")
        hook_state = {"last_status": None}
        temp_dir = self.file_manager.create_temp_directory(".yte-video-")
        try:
            def hook(data):
                self._check_cancel(cancellation_callback)
                status = data.get("status")
                if status != hook_state["last_status"]:
                    hook_state["last_status"] = status
                    logger.debug("yt-dlp hook | status=%s | arquivo=%s", status, data.get("filename"))
                if progress_callback:
                    progress_callback(data)

            options = self._build_options(os.path.join(temp_dir, "%(title)s.%(ext)s"), format, quality, True, hook)
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            self._check_cancel(cancellation_callback)

            candidates = self.file_manager.list_files(temp_dir, self.INTERMEDIATE_EXTENSIONS)
            if not candidates:
                raise FileNotFoundError("Arquivo de áudio baixado não foi encontrado no diretório temporário.")
            if len(candidates) > 1:
                logger.warning("Mais de um arquivo intermediário encontrado no download isolado: %s", candidates)
            source = candidates[0]
            final_path = self.file_manager.get_unique_output_path(title, format)
            final_filename = os.path.basename(final_path)

            if format == "aac":
                self._ffmpeg_aac(source, final_path, quality)
            else:
                shutil.move(source, final_path)

            artist, song = self.file_manager.extract_artist_and_song(title)
            logger.info("_download_video() concluído em %.2fs | arquivo=%s", time.perf_counter() - started_at, final_path)
            return {"success": True, "type": "video", "video_title": title, "video_author": author,
                    "artist": artist, "song": song, "filename": final_filename, "full_path": final_path,
                    "format": format, "quality": quality, "message": "Áudio extraído com sucesso!"}
        finally:
            self.file_manager.cleanup_directory(temp_dir)

    def _download_playlist(self, url, info, format, quality, progress_callback, cancellation_callback=None):
        started_at = time.perf_counter()
        playlist_title = info.get("title", "Unknown Playlist")
        entries = [entry for entry in (info.get("entries") or []) if entry]
        playlist_total = len(entries) or info.get("playlist_count") or info.get("n_entries") or 0
        logger.info("_download_playlist() iniciado | título=%s | entries=%s | total=%s", playlist_title, len(entries), playlist_total)
        if not entries:
            raise ValueError("A playlist não possui vídeos disponíveis para download.")

        playlist_dir = self.file_manager.sanitize_filename(playlist_title)
        playlist_path = os.path.join(self.file_manager.base_directory, playlist_dir)
        self.file_manager.ensure_directory_exists(playlist_path)
        hook_state = {"last_status": None, "first_downloading": False}

        def hook(data):
            self._check_cancel(cancellation_callback)
            enriched = dict(data)
            info_dict = data.get("info_dict") or {}
            index = info_dict.get("playlist_index") or data.get("playlist_index") or 0
            total = info_dict.get("n_entries") or data.get("n_entries") or playlist_total
            try:
                index, total = int(index), int(total)
            except (TypeError, ValueError):
                index, total = 0, playlist_total
            item_percent = self._percent(data)
            overall_percent = int(max(0, min(100, (((index - 1) + item_percent / 100) / total) * 100))) if total and index else item_percent
            status = data.get("status")
            if status != hook_state["last_status"]:
                hook_state["last_status"] = status
                logger.debug("yt-dlp playlist hook | status=%s | faixa=%s/%s | item=%s%% | overall=%s%%", status, index, total, item_percent, overall_percent)
            if status == "downloading" and not hook_state["first_downloading"]:
                hook_state["first_downloading"] = True
                logger.info("PRIMEIRO DOWNLOAD EFETIVO INICIADO | faixa=%s/%s", index, playlist_total)
            enriched.update({"playlist_index": index, "playlist_total": total, "item_percent": item_percent, "overall_percent": overall_percent})
            if progress_callback:
                progress_callback(enriched)

        download_started = time.perf_counter()
        with yt_dlp.YoutubeDL(self._build_options(os.path.join(playlist_path, "%(title)s.%(ext)s"), format, quality, True, hook)) as ydl:
            for position, entry in enumerate(entries, start=1):
                self._check_cancel(cancellation_callback)
                entry = dict(entry)
                entry["playlist_index"] = entry.get("playlist_index") or position
                entry["playlist_count"] = playlist_total
                entry["n_entries"] = playlist_total
                temp_dir = self.file_manager.create_temp_directory(f".yte-playlist-{position:04d}-")
                try:
                    options = self._build_options(os.path.join(temp_dir, "%(title)s.%(ext)s"), format, quality, True, hook)
                    ydl.params.update(options)
                    logger.debug("_download_playlist(): process_ie_result() faixa=%s/%s", position, playlist_total)
                    ydl.process_ie_result(entry, download=True, extra_info={"playlist": playlist_title,
                        "playlist_index": position, "playlist_autonumber": position, "n_entries": playlist_total})
                    candidates = self.file_manager.list_files(temp_dir, self.INTERMEDIATE_EXTENSIONS)
                    if not candidates:
                        raise FileNotFoundError(f"Arquivo da faixa {position} não foi encontrado no diretório temporário.")
                    source = candidates[0]
                    title = entry.get("title") or (entry.get("webpage_url_basename") or f"Faixa {position}")
                    final_path = self.file_manager.get_unique_output_path(title, format, playlist_path)
                    if format == "aac":
                        self._ffmpeg_aac(source, final_path, quality)
                    else:
                        shutil.move(source, final_path)
                finally:
                    self.file_manager.cleanup_directory(temp_dir)

        logger.info("_download_playlist(): processamento concluído em %.2fs", time.perf_counter() - download_started)
        self._check_cancel(cancellation_callback)
        logger.info("_download_playlist() concluído em %.2fs", time.perf_counter() - started_at)
        return {"success": True, "type": "playlist", "playlist_title": playlist_title,
                "playlist_count": playlist_total, "playlist_path": playlist_path,
                "format": format, "quality": quality, "message": "Playlist baixada com sucesso!"}
