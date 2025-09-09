import subprocess
import os

def convert_audio(input_path, output_path, output_format, quality_kbps):
    """
    Converte um arquivo de áudio para um formato e qualidade específicos usando FFmpeg.

    Args:
        input_path (str): O caminho para o arquivo de áudio de entrada.
        output_path (str): O caminho para salvar o arquivo de áudio convertido.
        output_format (str): O formato de saída desejado (ex: 'mp3', 'aac', 'wav', 'flac', 'm4a').
        quality_kbps (int): A taxa de bits (qualidade) desejada em kbps (ex: 64, 128, 192, 320).
    """
    command = [
        'ffmpeg',
        '-i', input_path,
        '-b:a', f'{quality_kbps}k',
        '-vn',
        '-y',
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Áudio convertido com sucesso para: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao converter áudio: {e}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print("Erro: FFmpeg não encontrado. Certifique-se de que está instalado e no PATH.")

if __name__ == '__main__':
    # Exemplo de uso:
    # Certifique-se de ter um arquivo de áudio de entrada para testar
    input_file = './Audios/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3'
    output_directory = './Audios'
    output_file_mp3 = os.path.join(output_directory, 'converted_audio_192kbps.mp3')
    output_file_wav = os.path.join(output_directory, 'converted_audio.wav')

    if not os.path.exists(input_file):
        print(f"Erro: Arquivo de entrada não encontrado: {input_file}")
    else:
        # Teste de conversão para MP3 192kbps
        convert_audio(input_file, output_file_mp3, 'mp3', 192)

        # Teste de conversão para WAV (qualidade padrão para WAV é lossless, então bitrate é ignorado)
        # Para WAV, FFmpeg geralmente não usa -b:a, mas para consistência com a função, mantemos.
        # A qualidade real será a melhor possível para WAV.
        convert_audio(input_file, output_file_wav, 'wav', 0) # 0 para indicar que bitrate não é relevante para WAV


