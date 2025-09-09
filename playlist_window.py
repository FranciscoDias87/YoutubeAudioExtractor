import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
                             QProgressBar, QTextEdit, QGroupBox, QGridLayout, 
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap
from integrated_audio_extractor_playlist import extract_audio_from_url

class PlaylistExtractorThread(QThread):
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
            self.progress_signal.emit("Iniciando extração de playlist...")
            
            # Usar a função integrada de extração de áudio com callback de progresso
            result = self.extract_audio_with_progress(
                url=self.url,
                output_directory=self.output_path,
                format=self.format,
                quality=self.quality
            )
            
            if result['success']:
                if result['type'] == 'playlist':
                    self.finished_signal.emit(result['playlist_title'], result['message'])
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

class PlaylistWindow(QMainWindow):
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
        self.setWindowTitle("YouTube Audio Extractor - Playlist")
        self.setFixedSize(800, 650)  # Tamanho fixo para melhor centralização
        
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
        url_group = QGroupBox("URL da Playlist")
        url_layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole aqui a URL da playlist do YouTube...")
        self.url_input.setMinimumHeight(35)
        url_layout.addWidget(self.url_input)
        
        # Informação sobre playlists
        info_label = QLabel("💡 Dica: Certifique-se de que a playlist seja pública para que o download funcione corretamente.")
        info_label.setStyleSheet("color: #6c757d; font-style: italic; margin: 5px;")
        info_label.setWordWrap(True)
        url_layout.addWidget(info_label)
        
        url_button_layout = QHBoxLayout()
        self.process_url_button = QPushButton("Processar Playlist")
        self.process_url_button.clicked.connect(self.process_url)
        self.process_url_button.setMinimumHeight(35)
        url_button_layout.addWidget(self.process_url_button)
        url_button_layout.addStretch()
        
        url_layout.addLayout(url_button_layout)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)
        
        # Grupo de informações da playlist
        info_group = QGroupBox("Informações da Playlist")
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("Título:"), 0, 0)
        self.title_label = QLabel("N/A")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label, 0, 1)
        
        info_layout.addWidget(QLabel("Criador:"), 1, 0)
        self.author_label = QLabel("N/A")
        info_layout.addWidget(self.author_label, 1, 1)
        
        info_layout.addWidget(QLabel("Número de Vídeos:"), 2, 0)
        self.count_label = QLabel("N/A")
        info_layout.addWidget(self.count_label, 2, 1)
        
        info_layout.addWidget(QLabel("Pasta de Destino:"), 3, 0)
        self.folder_label = QLabel("N/A")
        self.folder_label.setWordWrap(True)
        self.folder_label.setStyleSheet("color: #28a745; font-weight: bold;")
        info_layout.addWidget(self.folder_label, 3, 1)
        
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
        
        config_layout.addWidget(QLabel("Diretório Base:"), 2, 0)
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
        
        # Aviso sobre download de playlist
        warning_label = QLabel("⚠️ Aviso: O download de playlists pode demorar dependendo do número de vídeos. Certifique-se de ter espaço suficiente em disco.")
        warning_label.setStyleSheet("color: #dc3545; font-weight: bold; background-color: #f8d7da; padding: 10px; border: 1px solid #f5c6cb; border-radius: 5px; margin: 5px;")
        warning_label.setWordWrap(True)
        main_layout.addWidget(warning_label)
        
        # Botão de download
        self.download_button = QPushButton("Baixar Playlist Completa")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        self.download_button.setMinimumHeight(45)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
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
        title_label = QLabel("Download de Playlist")
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

    def center_on_screen(self):
        """Centralizar a janela na tela"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

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
                border-color: #2196F3;
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
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida.")
            return
        
        if not ("youtube.com" in url and "playlist" or "list=" in url):
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida de playlist do YouTube.")
            return
        
        self.log_message("Processando playlist...")
        
        try:
            import yt_dlp
            ydl_opts = {'quiet': True, 'extract_flat': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                title = info_dict.get('title', 'N/A')
                author = info_dict.get('uploader', 'N/A')
                
                # Verificar se é realmente uma playlist
                is_playlist = info_dict.get('_type') == 'playlist' or \
                             ('entries' in info_dict and len(info_dict['entries']) > 1)
                
                if not is_playlist:
                    QMessageBox.warning(self, "Aviso", "Esta URL não parece ser uma playlist. Use a opção 'Baixar Vídeo Único' no menu principal.")
                    return
                
                entries_count = len(info_dict.get('entries', []))
                
                self.title_label.setText(title)
                self.author_label.setText(author)
                self.count_label.setText(f"{entries_count} vídeos")
                
                # Mostrar pasta de destino
                from file_manager import FileManager
                file_manager = FileManager(self.output_directory)
                playlist_dir_name = file_manager.sanitize_filename(title)
                playlist_path = os.path.join(self.output_directory, playlist_dir_name)
                self.folder_label.setText(playlist_path)
                
                self.download_button.setEnabled(True)
                self.log_message(f"Playlist processada: {entries_count} vídeos encontrados")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar playlist: {str(e)}")
            self.log_message(f"Erro: {str(e)}")

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório Base")
        if directory:
            self.output_directory = directory
            self.output_label.setText(directory)
            
            # Atualizar pasta de destino se já tiver processado uma playlist
            if self.title_label.text() != "N/A":
                from file_manager import FileManager
                file_manager = FileManager(self.output_directory)
                playlist_dir_name = file_manager.sanitize_filename(self.title_label.text())
                playlist_path = os.path.join(self.output_directory, playlist_dir_name)
                self.folder_label.setText(playlist_path)

    def start_download(self):
        url = self.url_input.text().strip()
        format = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida.")
            return
        
        # Confirmação antes de iniciar download de playlist
        reply = QMessageBox.question(self, "Confirmar Download", 
                                   f"Você está prestes a baixar uma playlist completa.\\n"
                                   f"Isso pode demorar bastante tempo.\\n\\n"
                                   f"Deseja continuar?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.download_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.log_message("Iniciando download da playlist...")
        
        self.extractor_thread = PlaylistExtractorThread(url, self.output_directory, format, quality)
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

    def download_finished(self, playlist_name, message):
        self.log_message(f"{message} - {playlist_name}")
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        # Limpar o campo de URL após o download ser concluído
        self.url_input.clear()
        QMessageBox.information(self, "Sucesso", f"Playlist baixada com sucesso!\\nPasta: {playlist_name}")

    def download_error(self, error_message):
        self.log_message(f"Erro: {error_message}")
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        QMessageBox.critical(self, "Erro", f"Erro no download da playlist:\\n{error_message}")

    def log_message(self, message):
        self.status_log.append(f"[{self.get_timestamp()}] {message}")

    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

def main():
    """Função principal para testar a janela de playlist"""
    app = QApplication(sys.argv)
    window = PlaylistWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

