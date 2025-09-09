import yt_dlp
import os
from file_manager import FileManager
import time # Importar para simular atraso

def extract_audio_from_url(url, output_directory=None, format='mp3', quality='128K'):
    """
    Extrai o áudio de um vídeo ou playlist do YouTube com gerenciamento automático de arquivos e nomenclatura.

    Args:
        url (str): A URL do vídeo ou playlist do YouTube.
        output_directory (str): O diretório base para salvar os arquivos de áudio. Se None, usa ~/Audios.
        format (str): O formato de áudio desejado (ex: 'mp3', 'aac', 'wav', 'flac', 'm4a').
        quality (str): A qualidade do áudio (ex: '64K', '128K', '192K', '320K').
    
    Returns:
        dict: Informações sobre os arquivos extraídos ou erro.
    """
    file_manager = FileManager(output_directory)
    
    try:
        # Tentar extrair informações para verificar se é vídeo ou playlist
        ydl_opts_info = {
            'quiet': True,
            'extract_flat': True, # Não baixar, apenas extrair metadados
            'force_generic_extractor': True, # Forçar extrator genérico para playlists
        }
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        is_playlist = info_dict.get('_type') == 'playlist' or \
                      ('entries' in info_dict and len(info_dict['entries']) > 1)

        if is_playlist:
            playlist_title = info_dict.get('title', 'Unknown Playlist')
            print(f"Detectada playlist: {playlist_title}")

            playlist_dir_name = file_manager.sanitize_filename(playlist_title)
            playlist_output_path = os.path.join(file_manager.base_directory, playlist_dir_name)
            file_manager.ensure_directory_exists(playlist_output_path)

            # Download real dos áudios da playlist
            extract_audio_playlist(
                playlist_url=url,
                output_path=playlist_output_path,
                format=format,
                quality=quality
            )

            return {
                'success': True,
                'type': 'playlist',
                'playlist_title': playlist_title,
                'output_path': playlist_output_path,
                'message': 'Playlist baixada com sucesso!'
            }

        else:
            # Lógica para vídeo único (mantida do script anterior)
            video_title = info_dict.get('title', 'Unknown Video')
            video_author = info_dict.get('uploader', 'Unknown')
            
            print(f"Detectado vídeo: {video_title}")
            
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

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': quality,
                }],
                'outtmpl': os.path.join(file_manager.base_directory, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Renomear o arquivo baixado para o nome padronizado
            downloaded_files = [f for f in os.listdir(file_manager.base_directory) if f.startswith(info_dict.get('title', '')) and f.endswith(f'.{format}')]
            if downloaded_files:
                temp_file_path = os.path.join(file_manager.base_directory, downloaded_files[0])
                renamed_path = file_manager.rename_file(temp_file_path, video_title, format)
                final_filename = os.path.basename(renamed_path) if renamed_path else final_filename
                final_path = renamed_path if renamed_path else final_path

            artist, song = file_manager.extract_artist_and_song(video_title)
            
            return {
                'success': True,
                'type': 'video',
                'video_title': video_title,
                'video_author': video_author,
                'artist': artist,
                'song': song,
                'filename': final_filename,
                'full_path': final_path,
                'format': format,
                'quality': quality,
                'message': 'Vídeo baixado com sucesso!'
            }
        
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Erro na extração.'
        }

def list_formats(video_url):
    """Lista os formatos disponíveis para o vídeo ou playlist."""
    with yt_dlp.YoutubeDL({'listformats': True}) as ydl:
        ydl.download([video_url])

def extract_audio_playlist(playlist_url, output_path='.', format='mp3', quality='128K'):
    def progress_hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = downloaded_bytes / total_bytes * 100
                print(f"Progresso: {percent:.2f}%")
            else:
                print("Baixando...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': quality,
        }],
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'noplaylist': False,
        'progress_hooks': [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=True)
            print("Áudio(s) extraído(s) com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        print("Tente rodar a função list_formats para ver os formatos disponíveis para esta playlist.")

# Exemplo de uso:
if __name__ == '__main__':
    # Exemplo de uso para vídeo único
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' # Never Gonna Give You Up
    print("\n=== Teste de Extração de Vídeo Único ===")
    result_video = extract_audio_from_url(
        url=video_url,
        format='mp3',
        quality='192K'
    )
    print(result_video)

    # Exemplo de uso para playlist
    # Substitua pela URL de uma playlist real do YouTube
    playlist_url = 'https://www.youtube.com/playlist?list=PLWZUAkUIgAVYR6LjYB43PSngWR6YcmPOn' # Exemplo: Playlist de teste 2
    print("\n=== Teste de Extração de Playlist ===")
    result_playlist = extract_audio_from_url(
        url=playlist_url,
        format='mp3',
        quality='128K'
    )
    print(result_playlist)

    # Limpar arquivos temporários ou de teste se necessário
    # import shutil
    # if os.path.exists(os.path.join(os.path.expanduser("~"), "Audios")):
    #     shutil.rmtree(os.path.join(os.path.expanduser("~"), "Audios"))


