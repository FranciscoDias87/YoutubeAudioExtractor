import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
                             QProgressBar, QTextEdit, QGroupBox, QGridLayout, 
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap
from integrated_audio_extractor_playlist import extract_audio_from_url

class AudioExtractorThread(QThread):
    progress_signal = pyqtSignal(str)
    progress_percentage_signal = pyqtSignal(int)  # Novo sinal para progresso em porcentagem
    finished_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, output_path, format, quality):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.format = format
        self.quality = quality

    def run(self):
        try:
            self.progress_signal.emit("Iniciando extração de áudio...")
            
            # Usar a função integrada de extração de áudio com callback de progresso
            result = self.extract_audio_with_progress(
                url=self.url,
                output_directory=self.output_path,
                format=self.format,
                quality=self.quality
            )
            
            if result['success']:
                if result['type'] == 'video':
                    self.finished_signal.emit(result['filename'], result['message'])
                else:
                    self.finished_signal.emit(result.get('filename', 'Arquivo'), result['message'])
            else:
                self.error_signal.emit(result['error'])
                
        except Exception as e:
            self.error_signal.emit(f"Erro na extração: {str(e)}")
    
    def extract_audio_with_progress(self, url, output_directory=None, format='mp3', quality='128K'):
        """Versão modificada da função de extração com callback de progresso"""
        import yt_dlp
        import os
        from file_manager import FileManager
        
        # Inicializar o gerenciador de arquivos
        file_manager = FileManager(output_directory)
        
        try:
            # Primeiro, obter informações do vídeo sem baixar
            ydl_opts_info = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
            # Verificar se é playlist ou vídeo único
            if info_dict.get('_type') == 'playlist' or ('entries' in info_dict and len(info_dict['entries']) > 1):
                # Lógica para playlist
                playlist_title = info_dict.get('title', 'Unknown Playlist')
                playlist_author = info_dict.get('uploader', 'Unknown')
                
                # Criar diretório para a playlist
                playlist_dir_name = file_manager.sanitize_filename(playlist_title)
                playlist_path = os.path.join(file_manager.base_directory, playlist_dir_name)
                os.makedirs(playlist_path, exist_ok=True)
                
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        percent_str = d.get('_percent_str', 'N/A')
                        self.progress_signal.emit(f"Baixando: {percent_str}")
                        
                        # Extrair porcentagem numérica e emitir sinal
                        if percent_str != 'N/A' and '%' in percent_str:
                            try:
                                percent_value = int(float(percent_str.replace('%', '')))
                                self.progress_percentage_signal.emit(percent_value)
                            except (ValueError, TypeError):
                                pass
                    elif d['status'] == 'finished':
                        self.progress_signal.emit("Download concluído, processando...")
                        self.progress_percentage_signal.emit(100)
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': format,
                        'preferredquality': quality,
                    }],
                    'outtmpl': os.path.join(playlist_path, '%(title)s.%(ext)s'),
                    'noplaylist': False,
                    'progress_hooks': [progress_hook],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                return {
                    'success': True,
                    'type': 'playlist',
                    'playlist_title': playlist_title,
                    'playlist_path': playlist_path,
                    'message': 'Playlist baixada com sucesso!'
                }
            else:
                # Lógica para vídeo único
                video_title = info_dict.get('title', 'Unknown Video')
                video_author = info_dict.get('uploader', 'Unknown')
                
                final_filename = file_manager.generate_filename(video_title, format)
                final_path = os.path.join(file_manager.base_directory, final_filename)
                
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        percent_str = d.get('_percent_str', 'N/A')
                        self.progress_signal.emit(f"Baixando: {percent_str}")
                        
                        # Extrair porcentagem numérica e emitir sinal
                        if percent_str != 'N/A' and '%' in percent_str:
                            try:
                                percent_value = int(float(percent_str.replace('%', '')))
                                self.progress_percentage_signal.emit(percent_value)
                            except (ValueError, TypeError):
                                pass
                    elif d['status'] == 'finished':
                        self.progress_signal.emit("Download concluído, processando...")
                        self.progress_percentage_signal.emit(100)
                
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
                downloaded_files = [f for f in os.listdir(file_manager.base_directory) if f.startswith(video_title) and f.endswith(f'.{format}')]
                if downloaded_files:
                    temp_file_path = os.path.join(file_manager.base_directory, downloaded_files[0])
                    os.rename(temp_file_path, final_path)
                
                return {
                    'success': True,
                    'type': 'video',
                    'filename': final_filename,
                    'file_path': final_path,
                    'message': 'Áudio extraído com sucesso!'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Erro na extração: {str(e)}"
            }

class SingleVideoWindow(QMainWindow):
    # Sinal para voltar ao menu principal
    back_to_menu_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.output_directory = ""  # Correção: inicializa o atributo antes de usar
        self.init_ui()
        self.output_directory = os.path.join(os.path.expanduser("~"), "Audios")
        
        # Criar diretório de saída se não existir
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def init_ui(self):
        self.setWindowTitle("YouTube Audio Extractor - Vídeo Único")
        self.setFixedSize(800, 600)  # Tamanho fixo para melhor centralização
        
        # Centralizar na tela
        self.center_on_screen()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Cabeçalho com botão voltar
        self.create_header(main_layout)
        
        # Grupo de entrada de URL
        url_group = QGroupBox("URL do Vídeo")
        url_layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole aqui a URL do vídeo do YouTube...")
        self.url_input.setMinimumHeight(35)
        url_layout.addWidget(self.url_input)
        
        url_button_layout = QHBoxLayout()
        self.process_url_button = QPushButton("Processar URL")
        self.process_url_button.clicked.connect(self.process_url)
        self.process_url_button.setMinimumHeight(35)
        url_button_layout.addWidget(self.process_url_button)
        url_button_layout.addStretch()
        
        url_layout.addLayout(url_button_layout)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)
        
        # Grupo de informações
        info_group = QGroupBox("Informações do Vídeo")
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("Título:"), 0, 0)
        self.title_label = QLabel("N/A")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label, 0, 1)
        
        info_layout.addWidget(QLabel("Autor/Canal:"), 1, 0)
        self.author_label = QLabel("N/A")
        info_layout.addWidget(self.author_label, 1, 1)
        
        info_layout.addWidget(QLabel("Duração:"), 2, 0)
        self.duration_label = QLabel("N/A")
        info_layout.addWidget(self.duration_label, 2, 1)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Grupo de configurações
        config_group = QGroupBox("Configurações de Conversão")
        config_layout = QGridLayout()
        
        config_layout.addWidget(QLabel("Formato de Áudio:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "aac", "wav", "flac", "m4a"])
        self.format_combo.setCurrentText("mp3")
        config_layout.addWidget(self.format_combo, 0, 1)
        
        config_layout.addWidget(QLabel("Qualidade (kbps):"), 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["64", "128", "192", "320"])
        self.quality_combo.setCurrentText("128")
        config_layout.addWidget(self.quality_combo, 1, 1)
        
        config_layout.addWidget(QLabel("Diretório de Saída:"), 2, 0)
        output_layout = QHBoxLayout()
        self.output_label = QLabel(self.output_directory)
        self.output_label.setWordWrap(True)
        self.output_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        output_layout.addWidget(self.output_label)
        
        self.browse_button = QPushButton("Procurar")
        self.browse_button.clicked.connect(self.browse_output_directory)
        output_layout.addWidget(self.browse_button)
        
        config_layout.addLayout(output_layout, 2, 1)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Botão de download
        self.download_button = QPushButton("Baixar Áudio")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        self.download_button.setMinimumHeight(45)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        main_layout.addWidget(self.download_button)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        main_layout.addWidget(self.progress_bar)
        
        # Log de status
        status_label = QLabel("Log de Status:")
        status_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(status_label)
        
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(150)
        self.status_log.setReadOnly(True)
        self.status_log.setStyleSheet("background-color: #f8f8f8; font-family: monospace;")
        main_layout.addWidget(self.status_log)
        
        # Aplicar estilos gerais
        self.apply_styles()

    def center_on_screen(self):
        """Centralizar a janela na tela"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def create_header(self, main_layout):
        """Criar cabeçalho com título e botão voltar"""
        header_layout = QHBoxLayout()
        
        # Botão voltar
        self.back_button = QPushButton("← Voltar ao Menu")
        self.back_button.clicked.connect(self.back_to_menu)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        header_layout.addWidget(self.back_button)
        
        header_layout.addStretch()
        
        # Título
        title_label = QLabel("Download de Vídeo Único")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Espaço para balancear o layout
        spacer_widget = QWidget()
        spacer_widget.setMinimumWidth(120)
        header_layout.addWidget(spacer_widget)
        
        main_layout.addLayout(header_layout)

    def apply_styles(self):
        """Aplicar estilos CSS à janela"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
        """)

    def back_to_menu(self):
        """Emitir sinal para voltar ao menu principal"""
        self.back_to_menu_requested.emit()

    def process_url(self):
        url = self.url_input.text().strip()
        url = clean_video_url(url)  # Limpa a URL
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida.")
            return
        
        if not ("youtube.com" in url or "youtu.be" in url):
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida do YouTube.")
            return
        
        self.log_message("Processando URL...")
        
        try:
            import yt_dlp
            ydl_opts = {'quiet': True, 'extract_flat': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                title = info_dict.get('title', 'N/A')
                author = info_dict.get('uploader', 'N/A')
                duration = info_dict.get('duration', 0)
                
                # Verificar se não é uma playlist
                is_playlist = info_dict.get('_type') == 'playlist' or \
                             ('entries' in info_dict and len(info_dict['entries']) > 1)
                
                if is_playlist:
                    QMessageBox.warning(self, "Aviso", "Esta URL parece ser uma playlist. Use a opção 'Baixar Playlist' no menu principal.")
                    return
                
                self.title_label.setText(title)
                self.author_label.setText(author)
                
                # Formatar duração
                if duration > 0:
                    minutes = duration // 60
                    seconds = duration % 60
                    self.duration_label.setText(f"{minutes}:{seconds:02d}")
                else:
                    self.duration_label.setText("N/A")
                
                self.download_button.setEnabled(True)
                self.log_message("URL processada com sucesso!")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar URL: {str(e)}")
            self.log_message(f"Erro: {str(e)}")

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório de Saída")
        if directory:
            self.output_directory = directory
            self.output_label.setText(directory)

    def start_download(self):
        url = self.url_input.text().strip()
        url = clean_video_url(url)  # Limpa a URL
        format = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida.")
            return
        
        self.download_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.log_message("Iniciando download...")
        
        self.extractor_thread = AudioExtractorThread(url, self.output_directory, format, quality)
        self.extractor_thread.progress_signal.connect(self.update_progress)
        self.extractor_thread.progress_percentage_signal.connect(self.update_progress_percentage)
        self.extractor_thread.finished_signal.connect(self.download_finished)
        self.extractor_thread.error_signal.connect(self.download_error)
        self.extractor_thread.start()

    def update_progress(self, message):
        self.log_message(message)
    
    def update_progress_percentage(self, percentage):
        """Atualiza a barra de progresso com porcentagem específica"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(percentage)
        # Atualizar o texto da barra de progresso para mostrar a porcentagem
        self.progress_bar.setFormat(f"{percentage}%")
        # Só logar em marcos importantes (0%, 25%, 50%, 75%, 100%)
        if percentage in [0, 25, 50, 75, 100]:
            self.log_message(f"Progresso: {percentage}%")

    def download_finished(self, filename, message):
        self.log_message(f"{message} - {filename}")
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        # Limpar o campo de URL após o download ser concluído
        self.url_input.clear()
        QMessageBox.information(self, "Sucesso", f"Vídeo baixado com sucesso!\\nArquivo: {filename}")

    def download_error(self, error_message):
        self.log_message(f"Erro: {error_message}")
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        QMessageBox.critical(self, "Erro", f"Erro no download:\\n{error_message}")

    def log_message(self, message):
        self.status_log.append(f"[{self.get_timestamp()}] {message}")

    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

def clean_video_url(url):
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    query.pop('list', None)
    new_query = urllib.parse.urlencode(query, doseq=True)
    cleaned_url = urllib.parse.urlunparse(parsed._replace(query=new_query))
    return cleaned_url

def main():
    """Função principal para testar a janela de vídeo único"""
    app = QApplication(sys.argv)
    window = SingleVideoWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

