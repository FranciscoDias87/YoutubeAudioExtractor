$ErrorActionPreference = 'Stop'

Write-Host '== YouTubeAudioExtractor Windows Build ==' -ForegroundColor Cyan

python tools/prepare_ffmpeg.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o FFmpeg.' }

python -m PyInstaller --clean --noconfirm youtube_audio_extractor.spec
if ($LASTEXITCODE -ne 0) { throw 'Falha no PyInstaller.' }

$artifact = Join-Path $PSScriptRoot '..\dist\YouTubeAudioExtractor.exe'
if (-not (Test-Path $artifact)) {
    throw "Artefato final não encontrado: $artifact"
}

Write-Host "Artefato final: $artifact" -ForegroundColor Green
Write-Host 'FFmpeg foi incorporado ao executável pelo PyInstaller; a validação em runtime usa _MEIPASS.' -ForegroundColor Green
Write-Host 'Build concluído. Execute os testes de fumaça em uma máquina sem FFmpeg no PATH.' -ForegroundColor Yellow
