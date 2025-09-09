import sys
import os
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
                             QProgressBar, QTextEdit, QGroupBox, QGridLayout, 
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap
import yt_dlp
import subprocess

class AudioExtractorThread(QThread):
    progress_signal = pyqtSignal(str)
    progress_percentage_signal = pyqtSignal(int)  # Novo sinal para progresso em porcentagem
    finished_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, video_url, output_path, format, quality):
        super().__init__()
        self.video_url = video_url
        self.output_path = output_path
        self.format = format
        self.quality = quality

    def run(self):
        try:
            self.progress_signal.emit("Iniciando extração de áudio...")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': self.format,
                    'preferredquality': self.quality,
                }],
                'outtmpl': f'{self.output_path}/%(title)s.%(ext)s',
                'noplaylist': True,
                'progress_hooks': [self.progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.video_url, download=True)
                filename = f"{info_dict['title']}.{self.format}"
                self.finished_signal.emit(filename, "Áudio extraído com sucesso!")
                
        except Exception as e:
            self.error_signal.emit(f"Erro na extração: {str(e)}")

    def progress_hook(self, d):
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

class YouTubeAudioExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.output_directory = os.path.join(os.path.expanduser("~"), "Audios")
        self.init_ui()

        # Criar diretório de saída se não existir
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def init_ui(self):
        self.setWindowTitle("YouTube Audio Extractor")
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Título
        title_label = QLabel("YouTube Audio Extrator")        
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Grupo de entrada de URL
        url_group = QGroupBox("URL do Vídeo")
        url_layout = QVBoxLayout()
        
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole aqui a URL do vídeo do YouTube...")
        url_layout.addWidget(self.url_input)

        
        url_button_layout = QHBoxLayout()
        self.process_url_button = QPushButton("Processar URL")
        self.process_url_button.clicked.connect(self.process_url)
        url_button_layout.addWidget(self.process_url_button)
        url_button_layout.addStretch()
        
        url_layout.addLayout(url_button_layout)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)

                
        # Grupo de informações do vídeo
        info_group = QGroupBox("Informações do Vídeo")
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("Título:"), 0, 0)
        self.title_label = QLabel("N/A")
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label, 0, 1)
        
        info_layout.addWidget(QLabel("Autor:"), 1, 0)
        self.author_label = QLabel("N/A")
        info_layout.addWidget(self.author_label, 1, 1)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Grupo de configurações
        config_group = QGroupBox("Configurações de Conversão")
        config_layout = QGridLayout()
        
        config_layout.addWidget(QLabel("Formato:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "aac", "wav", "flac", "m4a"])
        config_layout.addWidget(self.format_combo, 0, 1)
        
        config_layout.addWidget(QLabel("Qualidade:"), 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["64", "128", "192", "320"])
        self.quality_combo.setCurrentText("128")
        config_layout.addWidget(self.quality_combo, 1, 1)
        
        config_layout.addWidget(QLabel("Diretório de Saída:"), 2, 0)
        output_layout = QHBoxLayout()
        self.output_label = QLabel(self.output_directory)
        self.output_label.setWordWrap(True)
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
        main_layout.addWidget(self.download_button)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Log de status
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(150)
        self.status_log.setReadOnly(True)
        main_layout.addWidget(self.status_log)

    def process_url(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida.")
            return
        
        self.log_message("Processando URL...")
        
        try:
            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                self.title_label.setText(info_dict.get('title', 'N/A'))
                self.author_label.setText(info_dict.get('uploader', 'N/A'))
                
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
        format = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida.")
            return
        
        self.download_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
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
        self.log_message(f"{message} - Arquivo: {filename}")
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        # Limpar o campo de URL após o download ser concluído
        self.url_input.clear()
        QMessageBox.information(self, "Sucesso", f"Download concluído!\nArquivo salvo: {filename}")

    def download_error(self, error_message):
        self.log_message(f"Erro: {error_message}")
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        QMessageBox.critical(self, "Erro", error_message)

    def log_message(self, message):
        self.status_log.append(f"[{self.get_timestamp()}] {message}")

    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

def main():
    app = QApplication(sys.argv)
    window = YouTubeAudioExtractorGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

