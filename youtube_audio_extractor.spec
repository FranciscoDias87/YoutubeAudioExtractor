# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

ffmpeg_binary = os.path.join('ffmpeg', 'ffmpeg.exe')
ffprobe_binary = os.path.join('ffmpeg', 'ffprobe.exe')

if not os.path.isfile(ffmpeg_binary):
    raise SystemExit(
        'FFmpeg não preparado. Execute: python tools/prepare_ffmpeg.py antes do PyInstaller.'
    )

ffmpeg_binaries = [(ffmpeg_binary, 'ffmpeg')]
if os.path.isfile(ffprobe_binary):
    ffmpeg_binaries.append((ffprobe_binary, 'ffmpeg'))

hidden_imports = [
    'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui', 'yt_dlp',
    'yt_dlp.extractor', 'yt_dlp.downloader', 'yt_dlp.postprocessor',
    'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna',
    'websockets', 'brotli', 'mutagen', 'pycryptodomex', 'file_manager',
    'app', 'app.services', 'app.services.youtube_service',
    'app.services.ffmpeg_manager', 'integrated_audio_extractor_playlist',
    'main_menu', 'single_video_window', 'playlist_window'
]

a = Analysis(
    ['app.py'], pathex=[], binaries=ffmpeg_binaries,
    datas=[('icons/*', 'icons')], hiddenimports=hidden_imports,
    hookspath=[], hooksconfig=[], runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas', 'PIL',
              'cv2', 'tensorflow', 'torch', 'sklearn'],
    win_no_prefer_redirects=False, win_private_assemblies=False,
    cipher=block_cipher, noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='YouTubeAudioExtractor', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=True,
    upx_exclude=[], runtime_tmpdir=None, console=False,
    disable_windowed_traceback=False, target_arch=None,
    codesign_identity=None, entitlements_file=None, version_file=None,
)

if hasattr(exe, 'manifest'):
    exe.manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="2.0.0.0" processorArchitecture="*" name="YouTubeAudioExtractor" type="win32" />
  <description>YouTube Audio Extractor - Baixe áudio de vídeos e playlists do YouTube</description>
  <dependency><dependentAssembly>
    <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*" />
  </dependentAssembly></dependency>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3"><security><requestedPrivileges>
    <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
  </requestedPrivileges></security></trustInfo>
</assembly>"""
