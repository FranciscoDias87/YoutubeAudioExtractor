"""Legacy compatibility helpers for YouTube extraction."""

from app.services.youtube_service import YouTubeService


def list_formats(video_url):
    """Lista os formatos disponíveis para o vídeo."""
    import yt_dlp

    with yt_dlp.YoutubeDL({'listformats': True}) as ydl:
        ydl.download([video_url])


def clean_video_url(url):
    """Remove parâmetros de playlist de uma URL do YouTube."""
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    query.pop('list', None)
    new_query = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def extract_audio(video_url, output_path=None, format='mp3', quality='128K'):
    """
    Extrai áudio usando o serviço centralizado da aplicação.

    ``output_path=None`` usa o diretório padrão ``~/Audio``.
    O parâmetro continua disponível para preservar compatibilidade com
    chamadas antigas do projeto.
    """
    service = YouTubeService(output_directory=output_path)
    return service.extract_audio(
        url=clean_video_url(video_url),
        format=format,
        quality=quality,
    )


if __name__ == '__main__':
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    result = extract_audio(video_url, format='mp3', quality='128K')

    if result.get('success'):
        print("\nExtração bem-sucedida!")
        print(f"Arquivo salvo: {result['filename']}")
        print(f"Caminho completo: {result['full_path']}")
    else:
        print(f"\nErro na extração: {result['error']}")
