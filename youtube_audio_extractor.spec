# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Definir dados adicionais que precisam ser incluídos
added_files = [
    # Incluir arquivos de configuração se necessário
    # ('caminho/origem', 'caminho/destino')
]

# Definir módulos ocultos que o PyInstaller pode não detectar automaticamente
hidden_imports = [
    'PyQt5.QtCore',
    'PyQt5.QtWidgets', 
    'PyQt5.QtGui',
    'yt_dlp',
    'yt_dlp.extractor',
    'yt_dlp.downloader',
    'yt_dlp.postprocessor',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'websockets',
    'brotli',
    'mutagen',
    'pycryptodomex',
    'file_manager',
    'integrated_audio_extractor_playlist',
    'main_menu',
    'single_video_window',
    'playlist_window'
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
      *added_files,
      ('icons/*', 'icons')
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],    
    excludes=[
        # Excluir módulos desnecessários para reduzir tamanho
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'sklearn'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YouTubeAudioExtractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False para aplicação GUI (sem console)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Adicionar caminho para ícone se disponível: icon='icon.ico'
    version_file=None,  # Adicionar arquivo de versão se necessário
)

# Configurações específicas para Windows
if hasattr(exe, 'manifest'):
    exe.manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="2.0.0.0"
    processorArchitecture="*"
    name="YouTubeAudioExtractor"
    type="win32"
  />
  <description>YouTube Audio Extractor - Baixe áudio de vídeos e playlists do YouTube</description>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="*"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>"""

