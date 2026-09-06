$ErrorActionPreference = 'Stop'

Write-Host '== YouTubeAudioExtractor Windows Build ==' -ForegroundColor Cyan

if (-not $env:YOUTUBE_AUDIO_EXTRACTOR_FFMPEG_SHA256) {
    throw 'Defina YOUTUBE_AUDIO_EXTRACTOR_FFMPEG_SHA256 antes do build.'
}

python tools/prepare_ffmpeg.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o FFmpeg.' }

python -m PyInstaller --clean --noconfirm youtube_audio_extractor.spec
if ($LASTEXITCODE -ne 0) { throw 'Falha no PyInstaller.' }

$bundled = Join-Path $PSScriptRoot '..\dist\YouTubeAudioExtractor\ffmpeg\ffmpeg.exe'
if (-not (Test-Path $bundled)) {
    throw "FFmpeg não foi incorporado ao artefato: $bundled"
}

& $bundled -version | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw 'FFmpeg incorporado não passou na validação.' }

Write-Host 'Build concluído: FFmpeg incorporado e validado.' -ForegroundColor Green
