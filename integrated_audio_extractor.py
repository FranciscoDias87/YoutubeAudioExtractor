import yt_dlp
import os
from file_manager import FileManager

def extract_audio_with_file_management(video_url, output_directory=None, format='mp3', quality='128'):
    """
    Extrai o áudio de um vídeo do YouTube com gerenciamento automático de arquivos e nomenclatura.

    Args:
        video_url (str): A URL do vídeo do YouTube.
        output_directory (str): O diretório para salvar o arquivo de áudio. Se None, usa ~/Audios.
        format (str): O formato de áudio desejado (ex: 'mp3', 'aac', 'wav', 'flac', 'm4a').
        quality (str): A qualidade do áudio (ex: '64', '128', '192', '320').
    
    Returns:
        dict: Informações sobre o arquivo extraído
    """
    # Inicializar o gerenciador de arquivos
    file_manager = FileManager(output_directory)
    
    try:
        # Primeiro, obter informações do vídeo sem baixar
        ydl_opts_info = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict['title']
            video_author = info_dict.get('uploader', 'Unknown')
        
        print(f"Título do vídeo: {video_title}")
        print(f"Autor: {video_author}")
        
        # Gerar nome do arquivo usando o gerenciador
        final_filename = file_manager.generate_filename(video_title, format)
        final_path = os.path.join(file_manager.base_directory, final_filename)
        
        print(f"Nome do arquivo final: {final_filename}")

        def progress_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                if total_bytes:
                    percent = downloaded_bytes / total_bytes * 100
                    print(f"Progresso: {percent:.2f}%")
                else:
                    print("Baixando...")

        # Configurar yt-dlp para baixar com nome temporário
        temp_filename = f"temp_%(title)s.%(ext)s"
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': quality,
            }],
            'outtmpl': os.path.join(file_manager.base_directory, temp_filename),
            'noplaylist': True,
            'progress_hooks': [progress_hook],
        }

        # Baixar o áudio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Encontrar o arquivo baixado (yt-dlp pode ter modificado o nome)
        downloaded_files = []
        for file in os.listdir(file_manager.base_directory):
            if file.startswith("temp_") and file.endswith(f".{format}"):
                downloaded_files.append(file)
        
        if not downloaded_files:
            raise Exception("Arquivo baixado não encontrado")
        
        # Assumir que o arquivo mais recente é o que acabamos de baixar
        temp_file_path = os.path.join(file_manager.base_directory, downloaded_files[-1])
        
        # Renomear para o nome final
        if os.path.exists(temp_file_path):
            # Verificar se o arquivo final já existe e criar nome único se necessário
            counter = 1
            base_final_path = final_path
            while os.path.exists(final_path):
                name, ext = os.path.splitext(base_final_path)
                final_path = f"{name} ({counter}){ext}"
                final_filename = os.path.basename(final_path)
                counter += 1
            
            os.rename(temp_file_path, final_path)
            print(f"Arquivo renomeado para: {final_filename}")
        
        # Extrair informações de artista e música para retorno
        artist, song = file_manager.extract_artist_and_song(video_title)
        
        return {
            'success': True,
            'video_title': video_title,
            'video_author': video_author,
            'artist': artist,
            'song': song,
            'filename': final_filename,
            'full_path': final_path,
            'format': format,
            'quality': quality
        }
        
    except Exception as e:
        print(f"Erro na extração: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    # Exemplo de uso
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Never Gonna Give You Up
    
    print("=== Teste de Extração Integrada ===")
    result = extract_audio_with_file_management(
        video_url=video_url,
        format='mp3',
        quality='192'
    )
    
    if result['success']:
        print("\n✅ Extração bem-sucedida!")
        print(f"Título: {result['video_title']}")
        print(f"Autor: {result['video_author']}")
        print(f"Artista extraído: {result['artist']}")
        print(f"Música extraída: {result['song']}")
        print(f"Arquivo salvo: {result['filename']}")
        print(f"Caminho completo: {result['full_path']}")
    else:
        print(f"\n❌ Erro na extração: {result['error']}")

