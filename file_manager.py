import os
import re
import unicodedata
from pathlib import Path

class FileManager:
    def __init__(self, base_directory=None):
        """
        Inicializa o gerenciador de arquivos.
        
        Args:
            base_directory (str): Diretório base para salvar os arquivos. 
                                 Se None, usa ~/Audios
        """
        if base_directory is None:
            self.base_directory = os.path.join(os.path.expanduser("~"), "Audios")
        else:
            self.base_directory = base_directory
        
        self.ensure_directory_exists(self.base_directory)
    
    def ensure_directory_exists(self, directory_path):
        """
        Garante que o diretório existe, criando-o se necessário.
        
        Args:
            directory_path (str): Caminho do diretório
        """
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    def extract_artist_and_song(self, video_title):
        """
        Extrai o nome do artista e da música do título do vídeo.
        
        Args:
            video_title (str): Título do vídeo do YouTube
            
        Returns:
            tuple: (artista, música) ou (None, título_limpo) se não conseguir extrair
        """
        # Limpar o título removendo informações extras comuns
        cleaned_title = self.clean_video_title(video_title)
        
        # Padrões comuns para separar artista e música
        patterns = [
            r'^(.+?)\s*[-–—]\s*(.+)$',  # Artista - Música
            r'^(.+?)\s*[:|]\s*(.+)$',   # Artista : Música ou Artista | Música
            r'^(.+?)\s*[""]\s*(.+?)\s*[""]\s*$',  # Artista "Música"
            r'^(.+?)\s*['']\s*(.+?)\s*['']\s*$',  # Artista 'Música'
            r'^(.+?)\s*\(\s*(.+?)\s*\)$',  # Artista (Música)
            r'^(.+?)\s*by\s+(.+)$',     # Música by Artista (inverso)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, cleaned_title, re.IGNORECASE)
            if match:
                part1, part2 = match.groups()
                part1, part2 = part1.strip(), part2.strip()
                
                # Para o padrão "by", inverter a ordem
                if 'by' in pattern:
                    return part2, part1
                else:
                    return part1, part2
        
        # Se não conseguir extrair, retorna None para artista e o título limpo
        return None, cleaned_title
    
    def clean_video_title(self, title):
        """
        Limpa o título do vídeo removendo informações extras.
        
        Args:
            title (str): Título original do vídeo
            
        Returns:
            str: Título limpo
        """
        # Remover informações comuns entre parênteses e colchetes
        patterns_to_remove = [
            r'\s*\([^)]*(?:official|video|audio|lyric|hd|4k|remaster|version)\s*[^)]*\)',
            r'\s*\[[^\]]*(?:official|video|audio|lyric|hd|4k|remaster|version)\s*[^\]]*\]',
            r'\s*\([^)]*\d{4}[^)]*\)',  # Anos entre parênteses
            r'\s*\[[^\]]*\d{4}[^\]]*\]',  # Anos entre colchetes
            r'\s*\(feat\.?[^)]*\)',     # Featuring
            r'\s*\[feat\.?[^\]]*\]',    # Featuring
            r'\s*ft\.?\s+[^-–—]*(?=[-–—])',  # ft. antes de separador
        ]
        
        cleaned = title
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Limpar espaços extras
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def sanitize_filename(self, filename):
        """
        Sanitiza o nome do arquivo removendo caracteres inválidos.
        
        Args:
            filename (str): Nome do arquivo original
            
        Returns:
            str: Nome do arquivo sanitizado
        """
        # Normalizar unicode
        filename = unicodedata.normalize('NFKD', filename)
        
        # Remover ou substituir caracteres inválidos para nomes de arquivo
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, '', filename)
        
        # Substituir múltiplos espaços por um único espaço
        filename = re.sub(r'\s+', ' ', filename)
        
        # Remover espaços no início e fim
        filename = filename.strip()
        
        # Limitar o comprimento (opcional, para evitar nomes muito longos)
        if len(filename) > 200:
            filename = filename[:200].strip()
        
        return filename
    
    def generate_filename(self, video_title, audio_format):
        """
        Gera o nome do arquivo seguindo o padrão: artista - música.formato
        
        Args:
            video_title (str): Título do vídeo
            audio_format (str): Formato do áudio (mp3, wav, etc.)
            
        Returns:
            str: Nome do arquivo formatado
        """
        artist, song = self.extract_artist_and_song(video_title)
        
        if artist and song:
            # Formato: artista - música.formato
            filename = f"{artist} - {song}"
        else:
            # Se não conseguir extrair, usa o título limpo
            filename = song  # song contém o título limpo quando artist é None
        
        # Sanitizar o nome do arquivo
        filename = self.sanitize_filename(filename)
        
        # Adicionar extensão
        return f"{filename}.{audio_format}"
    
    def get_full_path(self, video_title, audio_format):
        """
        Retorna o caminho completo para salvar o arquivo.
        
        Args:
            video_title (str): Título do vídeo
            audio_format (str): Formato do áudio
            
        Returns:
            str: Caminho completo do arquivo
        """
        filename = self.generate_filename(video_title, audio_format)
        return os.path.join(self.base_directory, filename)
    
    def rename_file(self, current_path, video_title, audio_format):
        """
        Renomeia um arquivo existente para seguir o padrão de nomenclatura.
        
        Args:
            current_path (str): Caminho atual do arquivo
            video_title (str): Título do vídeo
            audio_format (str): Formato do áudio
            
        Returns:
            str: Novo caminho do arquivo ou None se falhou
        """
        if not os.path.exists(current_path):
            print(f"Arquivo não encontrado: {current_path}")
            return None
        
        new_filename = self.generate_filename(video_title, audio_format)
        new_path = os.path.join(self.base_directory, new_filename)
        
        try:
            # Evitar sobrescrever arquivos existentes
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

# Exemplo de uso e testes
if __name__ == "__main__":
    # Criar instância do gerenciador
    file_manager = FileManager()
    
    # Testes de extração de artista e música
    test_titles = [
        "Rick Astley - Never Gonna Give You Up (Official Video)",
        "Queen: Bohemian Rhapsody (Official Video Remaster)",
        "The Beatles | Hey Jude",
        "Imagine Dragons - Believer (Official Music Video)",
        "Ed Sheeran 'Shape of You' [Official Video]",
        "Despacito by Luis Fonsi ft. Daddy Yankee",
        "Adele (Hello) Official Video",
        "Some Random Video Title Without Pattern",
        "Artist Name - Song Name (feat. Another Artist) [Official Audio 2023]"
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

