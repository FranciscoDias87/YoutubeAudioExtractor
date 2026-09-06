import urllib.parse

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout, QWidget, QApplication,
)

from app.controllers.download_controller import DownloadController
from file_manager import FileManager


class SingleVideoWindow(QMainWindow):
    """UI for single-video downloads; business logic lives in the controller."""

    back_to_menu_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.output_directory = FileManager().base_directory
        self.controller = DownloadController(self)
        self._video_metadata = None
        self.init_ui()
        self._connect_controller()

    def _connect_controller(self):
        self.controller.progress.connect(self.update_progress)
        self.controller.succeeded.connect(self.download_finished)
        self.controller.failed.connect(self.download_error)
        self.controller.started.connect(self._download_started)
        self.controller.finished.connect(self._download_finished)
        self.controller.metadata_succeeded.connect(self._metadata_loaded)
        self.controller.metadata_failed.connect(self._metadata_error)

    def init_ui(self):
        self.setWindowTitle("YouTube Audio Extractor - Vídeo Único")
        self.setFixedSize(800, 600)
        self.center_on_screen()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.create_header(main_layout)

        url_group = QGroupBox("URL do Vídeo")
        url_layout = QVBoxLayout(url_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole aqui a URL do vídeo do YouTube...")
        self.url_input.setMinimumHeight(35)
        url_layout.addWidget(self.url_input)
        row = QHBoxLayout()
        self.process_url_button = QPushButton("Processar URL")
        self.process_url_button.clicked.connect(self.process_url)
        self.process_url_button.setMinimumHeight(35)
        row.addWidget(self.process_url_button)
        row.addStretch()
        url_layout.addLayout(row)
        main_layout.addWidget(url_group)

        info_group = QGroupBox("Informações do Vídeo")
        info_layout = QGridLayout(info_group)
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
        main_layout.addWidget(info_group)

        config_group = QGroupBox("Configurações de Conversão")
        config_layout = QGridLayout(config_group)
        config_layout.addWidget(QLabel("Formato de Áudio:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "aac", "wav", "flac", "m4a"])
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
        main_layout.addWidget(config_group)

        self.download_button = QPushButton("Baixar Áudio")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        self.download_button.setMinimumHeight(45)
        self.download_button.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-size: 14px;
                          font-weight: bold; border: none; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        main_layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("Log de Status:"))
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(150)
        self.status_log.setReadOnly(True)
        self.status_log.setStyleSheet("background-color: #f8f8f8; font-family: monospace;")
        main_layout.addWidget(self.status_log)
        self.apply_styles()

    def create_header(self, main_layout):
        header_layout = QHBoxLayout()
        self.back_button = QPushButton("← Voltar ao Menu")
        self.back_button.clicked.connect(self.back_to_menu)
        header_layout.addWidget(self.back_button)
        header_layout.addStretch()
        title_label = QLabel("Download de Vídeo Único")
        title_label.setAlignment(Qt.AlignCenter)
        font = QFont(); font.setPointSize(18); font.setBold(True)
        title_label.setFont(font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        spacer = QWidget(); spacer.setMinimumWidth(120); header_layout.addWidget(spacer)
        main_layout.addLayout(header_layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #ffffff; }
            QGroupBox { font-weight: bold; border: 2px solid #cccccc; border-radius: 5px;
                        margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit { border: 2px solid #ddd; border-radius: 5px; padding: 5px; font-size: 12px; }
            QLineEdit:focus { border-color: #4CAF50; }
            QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px;
                          padding: 5px 10px; font-size: 12px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QComboBox { border: 1px solid #ccc; border-radius: 5px; padding: 5px; font-size: 12px; }
        """)

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def back_to_menu(self):
        self.back_to_menu_requested.emit()

    def process_url(self):
        url = clean_video_url(self.url_input.text())
        valid, error = self.controller.validate(url, self.format_combo.currentText(), self.quality_combo.currentText())
        if not valid:
            QMessageBox.warning(self, "Aviso", error)
            return

        self._video_metadata = None
        self.download_button.setEnabled(False)
        self.process_url_button.setEnabled(False)
        self.log_message("Processando URL em segundo plano...")
        self.controller.inspect_async(url, single=True)

    def _metadata_loaded(self, info):
        self._video_metadata = info
        self.title_label.setText(info.get("title", "N/A"))
        self.author_label.setText(info.get("uploader", "N/A"))
        self.duration_label.setText(format_duration(info.get("duration")))
        self.url_input.setText(clean_video_url(self.url_input.text()))
        self.download_button.setEnabled(True)
        self.process_url_button.setEnabled(True)
        self.log_message("URL processada com sucesso.")

    def _metadata_error(self, error):
        self._video_metadata = None
        self.download_button.setEnabled(False)
        self.process_url_button.setEnabled(True)
        self.log_message(f"Erro ao processar URL: {error}")
        QMessageBox.critical(self, "Erro", f"Não foi possível processar a URL:\n{error}")

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório", self.output_directory)
        if directory:
            self.output_directory = directory
            self.output_label.setText(directory)

    def start_download(self):
        url = clean_video_url(self.url_input.text())
        self.log_message("Iniciando download...")
        self.controller.download(
            url=url,
            output_directory=self.output_directory,
            audio_format=self.format_combo.currentText(),
            quality=self.quality_combo.currentText(),
            metadata=self._video_metadata,
        )

    def _download_started(self):
        self.download_button.setEnabled(False)
        self.process_url_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    def _download_finished(self):
        self.download_button.setEnabled(bool(self._video_metadata))
        self.process_url_button.setEnabled(True)
        self.browse_button.setEnabled(True)

    def update_progress(self, data):
        status = data.get("status")
        if status == "downloading":
            percent = self._progress_value(data)
            self.progress_bar.setValue(percent)
            self.log_message(f"Baixando: {data.get('_percent_str', f'{percent}%')}")
        elif status == "finished":
            self.progress_bar.setValue(100)
            self.log_message("Download concluído, processando...")

    @staticmethod
    def _progress_value(data):
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes", 0)
        return max(0, min(100, int(downloaded / total * 100))) if total else 0

    def download_finished(self, result):
        self.progress_bar.setValue(100)
        self.log_message(result.get("message", "Download concluído."))
        QMessageBox.information(self, "Sucesso", result.get("message", "Áudio extraído com sucesso!"))

    def download_error(self, error):
        self.log_message(f"Erro: {error}")
        QMessageBox.critical(self, "Erro", error)

    def log_message(self, message):
        from datetime import datetime
        self.status_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def clean_video_url(url):
    parsed = urllib.parse.urlparse((url or "").strip())
    query = urllib.parse.parse_qs(parsed.query)
    if "youtu.be" in parsed.netloc:
        return url.split("?")[0]
    if "youtube.com" in parsed.netloc and "v" in query:
        return f"https://www.youtube.com/watch?v={query['v'][0]}"
    return (url or "").strip()


def format_duration(seconds):
    if not seconds:
        return "N/A"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"
