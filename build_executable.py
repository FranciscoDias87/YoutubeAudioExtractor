#!/usr/bin/env python3
"""
Script para gerar executável do YouTube Audio Extractor para Windows
Autor: Manus AI
Versão: 2.0
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step_number, description):
    """Imprimir etapa do processo de build"""
    print(f"\n{'='*60}")
    print(f"ETAPA {step_number}: {description}")
    print(f"{'='*60}")

def run_command(command, description):
    """Executar comando e verificar resultado"""
    print(f"\n🔄 {description}...")
    print(f"Comando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} concluído com sucesso!")
        if result.stdout:
            print(f"Saída: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {description}:")
        print(f"Código de saída: {e.returncode}")
        print(f"Erro: {e.stderr}")
        return False

def check_dependencies():
    """Verificar se todas as dependências estão instaladas"""
    print_step(1, "VERIFICANDO DEPENDÊNCIAS")
    
    dependencies = [
        ('PyInstaller', 'PyInstaller'),
        ('PyQt5', 'PyQt5'),
        ('yt_dlp', 'yt-dlp')
    ]
    
    missing_deps = []
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name} está instalado")
        except ImportError:
            print(f"❌ {name} NÃO está instalado")
            missing_deps.append(name)
    
    if missing_deps:
        print(f"\n⚠️  Dependências faltando: {', '.join(missing_deps)}")
        print("Execute: pip install pyinstaller PyQt5 yt-dlp")
        return False
    
    print("\n✅ Todas as dependências estão instaladas!")
    return True

def clean_build_directories():
    """Limpar diretórios de build anteriores"""
    print_step(2, "LIMPANDO DIRETÓRIOS DE BUILD")
    
    directories_to_clean = ['build', 'dist', '__pycache__']
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            print(f"🗑️  Removendo diretório: {directory}")
            shutil.rmtree(directory)
        else:
            print(f"📁 Diretório {directory} não existe (OK)")
    
    print("\n✅ Limpeza concluída!")

def verify_source_files():
    """Verificar se todos os arquivos fonte estão presentes"""
    print_step(3, "VERIFICANDO ARQUIVOS FONTE")
    
    required_files = [
        'app.py',
        'main_menu.py',
        'single_video_window.py',
        'playlist_window.py',
        'integrated_audio_extractor_playlist.py',
        'file_manager.py',
        'youtube_audio_extractor.spec'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} NÃO ENCONTRADO")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Arquivos faltando: {', '.join(missing_files)}")
        return False
    
    print("\n✅ Todos os arquivos fonte estão presentes!")
    return True

def build_executable():
    """Gerar o executável usando PyInstaller"""
    print_step(4, "GERANDO EXECUTÁVEL")
    
    # Comando PyInstaller
    command = "python.exe -m PyInstaller youtube_audio_extractor.spec --clean --noconfirm"
    
    success = run_command(command, "Geração do executável")
    
    if success:
        # Verificar se o executável foi criado
        exe_path = os.path.join('dist', 'YouTubeAudioExtractor.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"\n🎉 Executável criado com sucesso!")
            print(f"📍 Localização: {os.path.abspath(exe_path)}")
            print(f"📏 Tamanho: {file_size:.1f} MB")
            return True
        else:
            print(f"\n❌ Executável não foi encontrado em {exe_path}")
            return False
    
    return False

def create_installer_info():
    """Criar arquivo de informações para instalação"""
    print_step(5, "CRIANDO INFORMAÇÕES DE INSTALAÇÃO")
    
    info_content = """# YouTube Audio Extractor - Informações de Instalação

## Sobre o Software
- **Nome:** YouTube Audio Extractor
- **Versão:** 2.0
- **Desenvolvido por:** Francisco Dias 
- **Descrição:** Ferramenta para extrair áudio de vídeos e playlists do YouTube

## Requisitos do Sistema
- **Sistema Operacional:** Windows 10 ou superior (64-bit)
- **Memória RAM:** Mínimo 4 GB (recomendado 8 GB)
- **Espaço em Disco:** Mínimo 500 MB livres
- **Conexão com Internet:** Necessária para download de vídeos

## Instalação
1. Baixe o arquivo `YouTubeAudioExtractor.exe`
2. Execute o arquivo como administrador (clique direito → "Executar como administrador")
3. Se aparecer aviso do Windows Defender, clique em "Mais informações" → "Executar assim mesmo"
4. O programa será executado diretamente (não requer instalação)

## Primeiro Uso
1. Execute o `YouTubeAudioExtractor.exe`
2. Escolha entre "Baixar Vídeo Único" ou "Baixar Playlist"
3. Cole a URL do YouTube no campo apropriado
4. Configure formato e qualidade desejados
5. Clique em "Baixar" e aguarde o processo

## Funcionalidades
- ✅ Download de vídeos únicos do YouTube
- ✅ Download de playlists completas
- ✅ Múltiplos formatos de áudio (MP3, AAC, WAV, FLAC, M4A)
- ✅ Qualidade configurável (64K a 320K)
- ✅ Nomenclatura inteligente "Artista - Música"
- ✅ Organização automática em pastas
- ✅ Interface gráfica intuitiva

## Solução de Problemas

### Erro "Windows protegeu seu PC"
- Clique em "Mais informações"
- Clique em "Executar assim mesmo"
- Isso acontece porque o executável não tem assinatura digital

### Erro de download "Sign in to confirm you're not a bot"
- Este erro ocorre quando o YouTube detecta muitas requisições
- Aguarde alguns minutos e tente novamente
- Use uma VPN se o problema persistir

### Erro "FFmpeg não encontrado"
- O FFmpeg está incluído no executável
- Se o erro persistir, reinicie o programa

### Programa não abre
- Execute como administrador
- Verifique se o antivírus não está bloqueando
- Verifique se tem espaço suficiente em disco

## Suporte
Para suporte técnico ou reportar bugs:
- Email: support@manus.ai
- Website: https://manus.ai

## Licença
Este software é fornecido "como está" para uso pessoal.
Respeite os termos de uso do YouTube e leis de direitos autorais locais.

---
Gerado automaticamente pelo script de build
Data: {datetime}
"""
    
    try:
        from datetime import datetime
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        with open('dist/LEIA-ME.txt', 'w', encoding='utf-8') as f:
            f.write(info_content.format(datetime=now_str))
        print("✅ Arquivo LEIA-ME.txt criado em dist/")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de informações: {e}")
        return False

def create_batch_launcher():
    """Criar arquivo batch para facilitar execução"""
    print_step(6, "CRIANDO LAUNCHER BATCH")
    
    batch_content = """@echo off
title YouTube Audio Extractor
echo.
echo ========================================
echo  YouTube Audio Extractor v2.0
echo  Desenvolvido por Francisco Dias
echo ========================================
echo.
echo Iniciando aplicacao...
echo.

REM Verificar se o executavel existe
if not exist "YouTubeAudioExtractor.exe" (
    echo ERRO: YouTubeAudioExtractor.exe nao encontrado!
    echo Certifique-se de que este arquivo .bat esta na mesma pasta do executavel.
    pause
    exit /b 1
)

REM Executar o programa
start "" "YouTubeAudioExtractor.exe"

REM Aguardar um pouco para verificar se iniciou
timeout /t 2 /nobreak >nul

echo.
echo Aplicacao iniciada com sucesso!
echo Voce pode fechar esta janela.
echo.
pause
"""
    
    try:
        with open('dist/Executar_YouTube_Audio_Extractor.bat', 'w', encoding='utf-8') as f:
            f.write(batch_content)
        print("✅ Arquivo batch criado em dist/")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar arquivo batch: {e}")
        return False

def show_final_summary():
    """Mostrar resumo final do build"""
    print_step(7, "RESUMO FINAL")
    
    print("🎉 BUILD CONCLUÍDO COM SUCESSO!")
    print("\n📁 Arquivos gerados na pasta 'dist/':")
    
    dist_path = Path('dist')
    if dist_path.exists():
        for file in dist_path.iterdir():
            if file.is_file():
                size = file.stat().st_size / (1024 * 1024)  # MB
                print(f"   📄 {file.name} ({size:.1f} MB)")
    
    print(f"\n📍 Localização completa: {os.path.abspath('dist')}")
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("1. Teste o executável em uma máquina Windows")
    print("2. Verifique se todas as funcionalidades estão funcionando")
    print("3. Distribua a pasta 'dist' completa para os usuários")
    print("4. Inclua o arquivo LEIA-ME.txt com instruções")
    
    print("\n⚠️  IMPORTANTE:")
    print("- O executável pode ser detectado como falso positivo por antivírus")
    print("- Instrua os usuários a executar como administrador se necessário")
    print("- Teste em diferentes versões do Windows antes da distribuição")

def main():
    """Função principal do script de build"""
    print("🔨 YOUTUBE AUDIO EXTRACTOR - GERADOR DE EXECUTÁVEL")
    print("=" * 60)
    print("Este script irá gerar um executável Windows standalone")
    print("do YouTube Audio Extractor usando PyInstaller.")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('app.py'):
        print("❌ ERRO: Execute este script no diretório do projeto!")
        print("   O arquivo 'app.py' deve estar presente.")
        sys.exit(1)
    
    # Executar etapas do build
    steps = [
        check_dependencies,
        clean_build_directories,
        verify_source_files,
        build_executable,
        create_installer_info,
        create_batch_launcher,
        show_final_summary
    ]
    
    for i, step in enumerate(steps, 1):
        try:
            success = step()
            if success is False:
                print(f"\n❌ FALHA NA ETAPA {i}")
                print("Build interrompido. Corrija os erros e tente novamente.")
                sys.exit(1)
        except Exception as e:
            print(f"\n❌ ERRO INESPERADO NA ETAPA {i}: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 BUILD FINALIZADO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    main()

