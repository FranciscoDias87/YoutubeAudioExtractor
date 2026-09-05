import os
import re
import unicodedata
from pathlib import Path


class FileManager:
    """Gerencia diretórios e nomes dos arquivos de áudio."""

    DEFAULT_DIRECTORY_NAME = "Audio"

    def __init__(self, base_directory=None):
        """
        Inicializa o gerenciador de arquivos.

        Args:
            base_directory (str): Diretório base para salvar os arquivos.
                                 Se None, usa ~/Audio.
        """
        if base_directory is None:
            self.base_directory = os.path.join(
                os.path.expanduser("~"), self.DEFAULT_DIRECTORY_NAME
            )
        else:
            self.base_directory = os.path.abspath(os.path.expanduser(base_directory))

        self.ensure_directory_exists(self.base_directory)

    def ensure_directory_exists(self, directory_path):
        """Garante que o diretório existe, criando-o se necessário."""
        Path(directory_path).mkdir(parents=True, exist_ok=True)

    def extract_artist_and_song(self, video_title):
        """Extrai o nome do artista e da música do título do vídeo."""
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
        """Limpa o título do vídeo removendo informações extras."""
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
        """Sanitiza um nome para uso seguro como arquivo ou diretório."""
        filename = unicodedata.normalize('NFKD', filename)
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()

        if len(filename) > 200:
            filename = filename[:200].strip()

        return filename

    def generate_filename(self, video_title, audio_format):
        """Gera o nome do arquivo no padrão artista - música.formato."""
        artist, song = self.extract_artist_and_song(video_title)

        if artist and song:
            filename = f"{artist} - {song}"
        else:
            filename = song

        filename = self.sanitize_filename(filename)
        return f"{filename}.{audio_format}"

    def get_full_path(self, video_title, audio_format):
        """Retorna o caminho completo para o arquivo."""
        return os.path.join(
            self.base_directory,
            self.generate_filename(video_title, audio_format),
        )

    def rename_file(self, current_path, video_title, audio_format):
        """Renomeia um arquivo existente para o padrão da aplicação."""
        if not os.path.exists(current_path):
            print(f"Arquivo não encontrado: {current_path}")
            return None

        new_filename = self.generate_filename(video_title, audio_format)
        new_path = os.path.join(self.base_directory, new_filename)

        try:
            counter = 1
            base_new_path = new_path
            while os.path.exists(new_path):
                name, ext = os.path.splitext(base_new_path)
                new_path = f"{name} ({counter}){ext}"
                counter += 1

            os.rename(current_path, new_path)
            print(f"Arquivo renomeado: {os.path.basename(new_path)}")
            return new_path
        except OSError as e:
            print(f"Erro ao renomear arquivo: {e}")
            return current_path


if __name__ == "__main__":
    file_manager = FileManager()

    test_titles = [
        "Rick Astley - Never Gonna Give You Up (Official Video)",
        "Queen: Bohemian Rhapsody (Official Video Remaster)",
        "The Beatles | Hey Jude",
        "Imagine Dragons - Believer (Official Music Video)",
        "Ed Sheeran 'Shape of You' [Official Video]",
        "Despacito by Luis Fonsi ft. Daddy Yankee",
        "Adele (Hello) Official Video",
        "Some Random Video Title Without Pattern",
        "Artist Name - Song Name (feat. Another Artist) [Official Audio 2023]",
    ]

    print("=== Testes de Extração de Artista e Música ===")
    for title in test_titles:
        artist, song = file_manager.extract_artist_and_song(title)
        filename = file_manager.generate_filename(title, "mp3")
        print(f"Título: {title}")
        print(f"Artista: {artist}")
        print(f"Música: {song}")
        print(f"Nome do arquivo: {filename}")
        print("-" * 50)
