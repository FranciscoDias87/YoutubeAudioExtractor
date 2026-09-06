"""Centralized YouTube extraction service."""

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime
from typing import Callable, Optional

import yt_dlp

from file_manager import FileManager


def _trace(message):
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [SERVICE] {message}", flush=True)


class DownloadCancelled(Exception):
    """Raised internally when an active download receives a cancel request."""


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
        codec = "m4a" if audio_format == "aac" else audio_format
        return {"key": "FFmpegExtractAudio", "preferredcodec": codec, "preferredquality": quality}

    @staticmethod
    def _postprocessor_args(audio_format: str) -> dict:
        return {}

    @staticmethod
    def _ffmpeg_aac(input_path: str, output_path: str, quality: str) -> None:
        bitrate = YouTubeService._normalize_quality(quality).lower()
        command = ["ffmpeg", "-y", "-i", input_path, "-vn", "-c:a", "aac", "-b:a", bitrate, "-f", "adts", output_path]
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    @staticmethod
    def _check_cancel(cancellation_callback: Optional[Callable[[], bool]]) -> None:
        if cancellation_callback and cancellation_callback():
            raise DownloadCancelled()

    def extract_audio(
        self,
        url: str,
        format: str = "mp3",
        quality: str = "128K",
        progress_callback: Optional[Callable[[dict], None]] = None,
        cancellation_callback: Optional[Callable[[], bool]] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Extract audio from a single video or playlist.

        ``metadata`` may contain the result previously produced by MetadataWorker.
        For playlists this avoids a second, potentially very expensive, playlist
        discovery pass.
        """
        started_at = time.perf_counter()
        url = (url or "").strip()
        format = (format or "mp3").lower().strip()
        _trace(f"extract_audio() iniciado | formato={format} | qualidade={quality} | metadata_reutilizado={metadata is not None}")
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
                _trace("Usando metadados fornecidos pelo MetadataWorker; extract_info() adicional será evitado.")
            else:
                info_started = time.perf_counter()
                _trace("Criando YoutubeDL para consulta de metadados do download...")
                with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": False}) as ydl:
                    _trace("extract_info() do download iniciado")
                    info = ydl.extract_info(url, download=False)
                _trace(f"extract_info() do download concluído em {time.perf_counter() - info_started:.2f}s")

            self._check_cancel(cancellation_callback)
            info_type = info.get("_type")
            _trace(f"Tipo retornado pelo yt-dlp: {info_type or 'video'}")
            if info_type == "playlist":
                result = self._download_playlist(url, info, format, quality, progress_callback, cancellation_callback)
            else:
                result = self._download_video(url, info, format, quality, progress_callback, cancellation_callback)
            _trace(f"extract_audio() concluído em {time.perf_counter() - started_at:.2f}s")
            return result
        except DownloadCancelled:
            _trace(f"Download cancelado após {time.perf_counter() - started_at:.2f}s")
            return {"success": False, "cancelled": True, "message": "Download cancelado pelo usuário."}
        except Exception as exc:
            _trace(f"ERRO após {time.perf_counter() - started_at:.2f}s: {exc}")
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

    def _download_video(self, url, info, format, quality, progress_callback, cancellation_callback=None):
        started_at = time.perf_counter()
        title = info.get("title", "Unknown Video")
        author = info.get("uploader", "Unknown")
        hook_state = {"last_status": None}

        def hook(data):
            self._check_cancel(cancellation_callback)
            status = data.get("status")
            if status != hook_state["last_status"]:
                hook_state["last_status"] = status
                _trace(f"yt-dlp hook | status={status} | arquivo={data.get('filename')}")
            if progress_callback:
                progress_callback(data)

        final_filename = self.file_manager.generate_filename(title, format)
        final_path = os.path.join(self.file_manager.base_directory, final_filename)
        options = self._build_options(os.path.join(self.file_manager.base_directory, "%(title)s.%(ext)s"), format, quality, True, hook)
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        self._check_cancel(cancellation_callback)

        if format == "aac":
            intermediate = self._find_downloaded_file(title, {".m4a", ".webm", ".opus", ".mp3", ".wav", ".flac"})
            if not intermediate:
                raise FileNotFoundError("Arquivo intermediário de áudio não encontrado para conversão AAC.")
            self._ffmpeg_aac(intermediate, final_path, quality)
            if os.path.abspath(intermediate) != os.path.abspath(final_path):
                os.remove(intermediate)
        else:
            candidates = [os.path.join(self.file_manager.base_directory, name) for name in os.listdir(self.file_manager.base_directory) if name.startswith(title) and name.lower().endswith(f".{format}")]
            if candidates:
                source = candidates[0]
                if os.path.abspath(source) != os.path.abspath(final_path):
                    renamed = self.file_manager.rename_file(source, title, format)
                    if renamed:
                        final_path = renamed
                        final_filename = os.path.basename(renamed)

        artist, song = self.file_manager.extract_artist_and_song(title)
        _trace(f"_download_video() concluído em {time.perf_counter() - started_at:.2f}s")
        return {"success": True, "type": "video", "video_title": title, "video_author": author, "artist": artist, "song": song, "filename": final_filename, "full_path": final_path, "format": format, "quality": quality, "message": "Áudio extraído com sucesso!"}

    def _find_downloaded_file(self, title: str, extensions: set[str]) -> Optional[str]:
        matches = []
        for name in os.listdir(self.file_manager.base_directory):
            path = os.path.join(self.file_manager.base_directory, name)
            if os.path.isfile(path) and name.startswith(title) and os.path.splitext(name)[1].lower() in extensions:
                matches.append(path)
        return matches[0] if matches else None

    def _download_playlist(self, url, info, format, quality, progress_callback, cancellation_callback=None):
        started_at = time.perf_counter()
        playlist_title = info.get("title", "Unknown Playlist")
        entries = [entry for entry in (info.get("entries") or []) if entry]
        playlist_total = len(entries) or info.get("playlist_count") or info.get("n_entries") or 0
        _trace(f"_download_playlist() iniciado | título={playlist_title} | entries={len(entries)} | total={playlist_total}")
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
                index = int(index)
                total = int(total)
            except (TypeError, ValueError):
                index, total = 0, playlist_total
            item_percent = self._percent(data)
            overall_percent = int(max(0, min(100, (((index - 1) + item_percent / 100) / total) * 100))) if total and index else item_percent
            status = data.get("status")
            if status != hook_state["last_status"]:
                hook_state["last_status"] = status
                _trace(f"yt-dlp playlist hook | status={status} | faixa={index}/{total} | item={item_percent}% | overall={overall_percent}%")
            if status == "downloading" and not hook_state["first_downloading"]:
                hook_state["first_downloading"] = True
                _trace(f"PRIMEIRO DOWNLOAD EFETIVO INICIADO | faixa={index}/{playlist_total}")
            enriched.update({"playlist_index": index, "playlist_total": total, "item_percent": item_percent, "overall_percent": overall_percent})
            if progress_callback:
                progress_callback(enriched)

        options = self._build_options(os.path.join(playlist_path, "%(title)s.%(ext)s"), format, quality, True, hook)
        _trace("_download_playlist(): processando entries previamente extraídas; nenhuma nova descoberta da playlist será feita.")
        download_started = time.perf_counter()
        with yt_dlp.YoutubeDL(options) as ydl:
            for position, entry in enumerate(entries, start=1):
                self._check_cancel(cancellation_callback)
                entry = dict(entry)
                entry["playlist_index"] = entry.get("playlist_index") or position
                entry["playlist_count"] = playlist_total
                entry["n_entries"] = playlist_total
                _trace(f"_download_playlist(): process_ie_result() faixa={position}/{playlist_total}")
                ydl.process_ie_result(
                    entry,
                    download=True,
                    extra_info={
                        "playlist": playlist_title,
                        "playlist_index": position,
                        "playlist_autonumber": position,
                        "n_entries": playlist_total,
                    },
                )
        _trace(f"_download_playlist(): processamento concluído em {time.perf_counter() - download_started:.2f}s")
        self._check_cancel(cancellation_callback)

        if format == "aac":
            for name in os.listdir(playlist_path):
                self._check_cancel(cancellation_callback)
                source = os.path.join(playlist_path, name)
                if not os.path.isfile(source) or os.path.splitext(name)[1].lower() not in {".m4a", ".webm", ".opus", ".mp3", ".wav", ".flac"}:
                    continue
                output = os.path.splitext(source)[0] + ".aac"
                self._ffmpeg_aac(source, output, quality)
                os.remove(source)

        _trace(f"_download_playlist() concluído em {time.perf_counter() - started_at:.2f}s")
        return {"success": True, "type": "playlist", "playlist_title": playlist_title, "playlist_count": playlist_total, "playlist_path": playlist_path, "format": format, "quality": quality, "message": "Playlist baixada com sucesso!"}
