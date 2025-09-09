import yt_dlp

def list_formats(video_url):
    """Lista os formatos disponíveis para o vídeo."""
    with yt_dlp.YoutubeDL({'listformats': True}) as ydl:
        ydl.download([video_url])

def clean_video_url(url):
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    query.pop('list', None)
    new_query = urllib.parse.urlencode(query, doseq=True)
    cleaned_url = urllib.parse.urlunparse(parsed._replace(query=new_query))
    return cleaned_url

def extract_audio(video_url, output_path='.', format='mp3', quality='128K'):
    """
    Extrai o áudio de um vídeo do YouTube e o salva em um formato e qualidade específicos.
    """
    video_url = clean_video_url(video_url)  # Limpa a URL

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': quality,
        }],
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'progress_hooks': [lambda d: print(d['status'])],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            print(f"Áudio extraído com sucesso: {info_dict['title']}.{format}")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        print("Tente rodar a função list_formats para ver os formatos disponíveis para este vídeo.")

if __name__ == '__main__':
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    output_directory = './Audios'
    audio_format = 'mp3'
    audio_quality = '128K'

    import os
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Se ocorrer erro de formato, rode esta linha para listar os formatos disponíveis:
    # list_formats(video_url)

    extract_audio(video_url, output_directory, audio_format, audio_quality)


