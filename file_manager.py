import os
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path


class FileManager:
    """Gerencia diretórios, nomes e movimentação segura dos arquivos de áudio."""

    DEFAULT_DIRECTORY_NAME = "Audio"
    LEGACY_DIRECTORY_NAME = "Audios"
    AUDIO_EXTENSIONS = {".m4a", ".webm", ".opus", ".mp3", ".wav", ".flac", ".aac"}

    def __init__(self, base_directory=None):
        home_directory = os.path.expanduser("~")
        default_directory = os.path.join(home_directory, self.DEFAULT_DIRECTORY_NAME)

        if base_directory is None:
            self.base_directory = default_directory
        else:
            requested_directory = os.path.abspath(os.path.expanduser(base_directory))
            legacy_directory = os.path.join(home_directory, self.LEGACY_DIRECTORY_NAME)
            if os.path.normcase(requested_directory) == os.path.normcase(os.path.abspath(legacy_directory)):
                requested_directory = default_directory
            self.base_directory = requested_directory

        self.ensure_directory_exists(self.base_directory)

    def ensure_directory_exists(self, directory_path):
        Path(directory_path).mkdir(parents=True, exist_ok=True)

    def create_temp_directory(self, prefix=".yte-"):
        """Cria um diretório temporário isolado dentro do diretório de saída."""
        self.ensure_directory_exists(self.base_directory)
        return tempfile.mkdtemp(prefix=prefix, dir=self.base_directory)

    def cleanup_directory(self, directory_path):
        """Remove um diretório temporário e seu conteúdo, se existir."""
        if directory_path and os.path.isdir(directory_path):
            shutil.rmtree(directory_path, ignore_errors=True)

    def list_files(self, directory_path, extensions=None):
        """Lista somente arquivos do diretório informado, sem varrer diretórios externos."""
        allowed = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in (extensions or self.AUDIO_EXTENSIONS)}
        directory = Path(directory_path)
        if not directory.is_dir():
            return []
        return [
            str(path)
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in allowed
        ]

    def get_unique_path(self, directory_path, filename):
        """Retorna um caminho livre, adicionando sufixo numérico quando necessário."""
        self.ensure_directory_exists(directory_path)
        filename = self.sanitize_filename(filename)
        base, extension = os.path.splitext(filename)
        candidate = os.path.join(directory_path, filename)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(directory_path, f"{base} ({counter}){extension}")
            counter += 1
        return candidate

    def move_file(self, source_path, destination_directory, filename=None):
        """Move um arquivo para o destino usando caminho único e retorna o caminho final."""
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")
        self.ensure_directory_exists(destination_directory)
        target_name = filename or os.path.basename(source_path)
        destination_path = self.get_unique_path(destination_directory, target_name)
        return shutil.move(source_path, destination_path)

    def extract_artist_and_song(self, video_title):
        cleaned_title = self.clean_video_title(video_title)
        patterns = [
            r'^(.+?)\s*[-–—]\s*(.+)$',
            r'^(.+?)\s*[:|]\s*(.+)$',
            r'^(.+?)\s*[""]\s*(.+?)\s*[""]\s*$',
            r"^(.+?)\s*['']\s*(.+?)\s*['']\s*$",
            r'^(.+?)\s*\(\s*(.+?)\s*\)$',
            r'^(.+?)\s*by\s+(.+)$',
        ]
        for pattern in patterns:
            match = re.match(pattern, cleaned_title, re.IGNORECASE)
            if match:
                part1, part2 = (part.strip() for part in match.groups())
                if "by" in pattern:
                    return part2, part1
                return part1, part2
        return None, cleaned_title

    def clean_video_title(self, title):
        patterns_to_remove = [
            r'\s*\([^)]*(?:official|video|audio|lyric|hd|4k|remaster|version)\s*[^)]*\)',
            r'\s*\[[^\]]*(?:official|video|audio|lyric|hd|4k|remaster|version)\s*[^\]]*\]',
            r'\s*\([^)]*\d{4}[^)]*\)',
            r'\s*\[[^\]]*\d{4}[^\]]*\]',
            r'\s*\(feat\.?[^)]*\)',
            r'\s*\[feat\.?[^\]]*\]',
            r'\s*ft\.?\s+[^-–—]*(?=[-–—])',
        ]
        cleaned = title
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', cleaned).strip()

    def sanitize_filename(self, filename):
        filename = unicodedata.normalize('NFKD', filename)
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()
        filename = filename.rstrip('. ')
        if len(filename) > 200:
            filename = filename[:200].strip().rstrip('. ')
        return filename or "audio"

    def generate_filename(self, video_title, audio_format):
        artist, song = self.extract_artist_and_song(video_title)
        filename = f"{artist} - {song}" if artist and song else song
        filename = self.sanitize_filename(filename)
        return f"{filename}.{audio_format}"

    def get_full_path(self, video_title, audio_format):
        return os.path.join(self.base_directory, self.generate_filename(video_title, audio_format))

    def get_unique_output_path(self, video_title, audio_format, directory=None):
        directory = directory or self.base_directory
        return self.get_unique_path(directory, self.generate_filename(video_title, audio_format))

    def rename_file(self, current_path, video_title, audio_format):
        """Mantém compatibilidade com a API antiga, agora usando movimentação segura."""
        if not os.path.exists(current_path):
            return None
        destination_directory = os.path.dirname(os.path.abspath(current_path))
        target = self.get_unique_output_path(video_title, audio_format, destination_directory)
        try:
            return shutil.move(current_path, target)
        except OSError:
            return current_path


if __name__ == "__main__":
    file_manager = FileManager()
    print("Diretório de saída:", file_manager.base_directory)
