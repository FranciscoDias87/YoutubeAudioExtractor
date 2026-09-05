import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from app.controllers.download_controller import DownloadController
from file_manager import FileManager


class PlaylistWindow(QMainWindow):
    """UI for playlist downloads; operations are delegated to workers/controller."""

    back_to_menu_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.output_directory = FileManager().base_directory
        self.controller = DownloadController(self)
        self._playlist_total = 0
        self._playlist_current = 0
        self.init_ui()
        self._connect_controller()

    def _connect_controller(self):
        self.controller.progress.connect(self.update_progress)
        self.controller.succeeded.connect(self.download_finished)
        self.controller.failed.connect(self.download_error)
        self.controller.cancelled.connect(self.download_cancelled)
        self.controller.started.connect(self._download_started)
        self.controller.finished.connect(self._download_finished)
        self.controller.metadata_succeeded.connect(self._metadata_loaded)
        self.controller.metadata_failed.connect(self._metadata_error)

    def init_ui(self):
        self.setWindowTitle("YouTube Audio Extractor - Playlist")
        self.setFixedSize(800, 700)
        self.center_on_screen()
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.create_header(main_layout)

        url_group = QGroupBox("URL da Playlist")
        url_layout = QVBoxLayout(url_group)
        self.url_input = QLineEdit(); self.url_input.setPlaceholderText("Cole aqui a URL da playlist do YouTube..."); self.url_input.setMinimumHeight(35)
        url_layout.addWidget(self.url_input)
        info = QLabel("💡 Dica: Certifique-se de que a playlist seja pública para que o download funcione corretamente."); info.setStyleSheet("color: #6c757d; font-style: italic; margin: 5px;"); info.setWordWrap(True); url_layout.addWidget(info)
        row = QHBoxLayout()
        self.process_url_button = QPushButton("Processar Playlist"); self.process_url_button.clicked.connect(self.process_url); self.process_url_button.setMinimumHeight(35); row.addWidget(self.process_url_button)
        row.addStretch(); url_layout.addLayout(row); main_layout.addWidget(url_group)

        info_group = QGroupBox("Informações da Playlist")
        info_layout = QGridLayout(info_group)
        info_layout.addWidget(QLabel("Título:"), 0, 0); self.title_label = QLabel("N/A"); self.title_label.setWordWrap(True); self.title_label.setStyleSheet("font-weight: bold;"); info_layout.addWidget(self.title_label, 0, 1)
        info_layout.addWidget(QLabel("Criador:"), 1, 0); self.author_label = QLabel("N/A"); info_layout.addWidget(self.author_label, 1, 1)
        info_layout.addWidget(QLabel("Número de Vídeos:"), 2, 0); self.count_label = QLabel("N/A"); self.count_label.setStyleSheet("font-weight: bold;"); info_layout.addWidget(self.count_label, 2, 1)
        info_layout.addWidget(QLabel("Pasta de Destino:"), 3, 0); self.folder_label = QLabel("N/A"); self.folder_label.setWordWrap(True); self.folder_label.setStyleSheet("color: #28a745; font-weight: bold;"); info_layout.addWidget(self.folder_label, 3, 1)
        main_layout.addWidget(info_group)

        config_group = QGroupBox("Configurações de Conversão")
        config_layout = QGridLayout(config_group)
        config_layout.addWidget(QLabel("Formato de Áudio:"), 0, 0); self.format_combo = QComboBox(); self.format_combo.addItems(["mp3", "aac", "wav", "flac", "m4a"]); config_layout.addWidget(self.format_combo, 0, 1)
        config_layout.addWidget(QLabel("Qualidade (kbps):"), 1, 0); self.quality_combo = QComboBox(); self.quality_combo.addItems(["64", "128", "192", "320"]); self.quality_combo.setCurrentText("128"); config_layout.addWidget(self.quality_combo, 1, 1)
        config_layout.addWidget(QLabel("Diretório Base:"), 2, 0)
        output_layout = QHBoxLayout(); self.output_label = QLabel(self.output_directory); self.output_label.setWordWrap(True); self.output_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;"); output_layout.addWidget(self.output_label)
        self.browse_button = QPushButton("Procurar"); self.browse_button.clicked.connect(self.browse_output_directory); output_layout.addWidget(self.browse_button); config_layout.addLayout(output_layout, 2, 1); main_layout.addWidget(config_group)

        warning = QLabel("⚠️ Aviso: O download de playlists pode demorar dependendo do número de vídeos. Certifique-se de ter espaço suficiente em disco."); warning.setStyleSheet("color: #dc3545; font-weight: bold; background-color: #f8d7da; padding: 10px; border: 1px solid #f5c6cb; border-radius: 5px; margin: 5px;"); warning.setWordWrap(True); main_layout.addWidget(warning)

        buttons = QHBoxLayout()
        self.download_button = QPushButton("Baixar Playlist Completa"); self.download_button.clicked.connect(self.start_download); self.download_button.setEnabled(False); self.download_button.setMinimumHeight(45)
        self.cancel_button = QPushButton("Cancelar Download"); self.cancel_button.clicked.connect(self.cancel_download); self.cancel_button.setEnabled(False); self.cancel_button.setMinimumHeight(45)
        buttons.addWidget(self.download_button); buttons.addWidget(self.cancel_button); main_layout.addLayout(buttons)

        self.progress_label = QLabel("Progresso da playlist: aguardando..."); self.progress_label.setStyleSheet("font-weight: bold;"); main_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar(); self.progress_bar.setVisible(False); self.progress_bar.setMinimumHeight(25); main_layout.addWidget(self.progress_bar)
        self.item_progress_label = QLabel("Faixa atual: aguardando..."); main_layout.addWidget(self.item_progress_label)
        self.item_progress_bar = QProgressBar(); self.item_progress_bar.setVisible(False); main_layout.addWidget(self.item_progress_bar)
        main_layout.addWidget(QLabel("Log de Status:")); self.status_log = QTextEdit(); self.status_log.setMaximumHeight(130); self.status_log.setReadOnly(True); self.status_log.setStyleSheet("background-color: #f8f8f8; font-family: monospace;"); main_layout.addWidget(self.status_log)
        self.apply_styles()

    def create_header(self, main_layout):
        header = QHBoxLayout(); self.back_button = QPushButton("← Voltar ao Menu"); self.back_button.clicked.connect(self.back_to_menu); header.addWidget(self.back_button); header.addStretch()
        title = QLabel("Download de Playlist"); title.setAlignment(Qt.AlignCenter); font = QFont(); font.setPointSize(18); font.setBold(True); title.setFont(font); header.addWidget(title); header.addStretch(); spacer = QWidget(); spacer.setMinimumWidth(120); header.addWidget(spacer); main_layout.addLayout(header)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #ffffff; }
            QGroupBox { font-weight: bold; border: 2px solid #cccccc; border-radius: 5px; margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit { border: 2px solid #ddd; border-radius: 5px; padding: 5px; font-size: 12px; }
            QLineEdit:focus { border-color: #2196F3; }
            QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; padding: 5px 10px; font-size: 12px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QComboBox { border: 1px solid #ccc; border-radius: 5px; padding: 5px; font-size: 12px; }
        """)

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry(); self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
    def back_to_menu(self): self.back_to_menu_requested.emit()

    def process_url(self):
        url = (self.url_input.text() or "").strip()
        valid, error = self.controller.validate(url, self.format_combo.currentText(), self.quality_combo.currentText())
        if not valid: QMessageBox.warning(self, "Aviso", error); return
        self.log_message("Processando playlist em segundo plano...")
        self.process_url_button.setEnabled(False); self.download_button.setEnabled(False); self.count_label.setText("Consultando...")
        self.controller.inspect_async(url, single=False)

    def _metadata_loaded(self, info):
        self.process_url_button.setEnabled(True)
        self.title_label.setText(info.get("title", "N/A")); self.author_label.setText(info.get("uploader", "N/A"))
        entries = [entry for entry in (info.get("entries") or []) if entry]
        count = len(entries) or info.get("playlist_count") or info.get("n_entries")
        self._playlist_total = int(count or 0)
        self.count_label.setText(str(self._playlist_total) if self._playlist_total else "Não informado")
        playlist_title = info.get("title", "Playlist")
        self.folder_label.setText(os.path.join(self.output_directory, FileManager().sanitize_filename(playlist_title)))
        self.download_button.setEnabled(True)
        self.log_message(f"Playlist processada: {self._playlist_total or 'quantidade não informada'} vídeo(s).")

    def _metadata_error(self, error):
        self.process_url_button.setEnabled(True); self.download_button.setEnabled(False); self.count_label.setText("N/A")
        self.log_message(f"Erro ao processar playlist: {error}"); QMessageBox.critical(self, "Erro", f"Não foi possível processar a playlist:\n{error}")

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório", self.output_directory)
        if directory: self.output_directory = directory; self.output_label.setText(directory)

    def start_download(self):
        self.log_message("Iniciando download da playlist...")
        self._playlist_current = 0
        self.controller.download(self.url_input.text().strip(), self.output_directory, self.format_combo.currentText(), self.quality_combo.currentText())

    def cancel_download(self):
        if self.controller.cancel():
            self.cancel_button.setEnabled(False); self.progress_label.setText("Cancelando download..."); self.log_message("Solicitação de cancelamento enviada...")

    def _download_started(self):
        self.download_button.setEnabled(False); self.process_url_button.setEnabled(False); self.browse_button.setEnabled(False); self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0)
        self.item_progress_bar.setVisible(True); self.item_progress_bar.setRange(0, 100); self.item_progress_bar.setValue(0)
        self.progress_label.setText("Progresso da playlist: iniciando...")
        self.item_progress_label.setText("Faixa atual: iniciando...")

    def _download_finished(self):
        self.download_button.setEnabled(bool(self.url_input.text().strip()) and self._playlist_total > 0); self.process_url_button.setEnabled(True); self.browse_button.setEnabled(True); self.cancel_button.setEnabled(False)

    def update_progress(self, data):
        if data.get("status") not in {"downloading", "finished"}: return
        total = int(data.get("playlist_total") or self._playlist_total or 0); index = int(data.get("playlist_index") or 0)
        item_percent = int(data.get("item_percent", self._progress_value(data)))
        overall_percent = int(data.get("overall_percent", item_percent))
        if total: self._playlist_total = total
        if index: self._playlist_current = index
        self.progress_bar.setValue(overall_percent); self.progress_label.setText(f"Progresso da playlist: {self._playlist_current or '?'} de {self._playlist_total or '?'} vídeos — {overall_percent}%")
        self.item_progress_bar.setValue(item_percent)
        title = (data.get("info_dict") or {}).get("title", "faixa atual")
        self.item_progress_label.setText(f"Faixa atual: {title} — {item_percent}%")

    @staticmethod
    def _progress_value(data):
        total = data.get("total_bytes") or data.get("total_bytes_estimate"); downloaded = data.get("downloaded_bytes", 0)
        return max(0, min(100, int(downloaded / total * 100))) if total else 0

    def download_finished(self, result):
        self.progress_bar.setValue(100); self.item_progress_bar.setValue(100); self.progress_label.setText(f"Progresso da playlist: {result.get('playlist_count', self._playlist_total)} de {result.get('playlist_count', self._playlist_total)} vídeos — 100%"); self.log_message(result.get("message", "Playlist baixada com sucesso!")); QMessageBox.information(self, "Sucesso", result.get("message", "Playlist baixada com sucesso!"))

    def download_cancelled(self):
        self.log_message("Download cancelado pelo usuário."); self.progress_label.setText("Download cancelado."); self.item_progress_label.setText("Faixa atual: cancelada."); self.cancel_button.setEnabled(False); QMessageBox.information(self, "Download cancelado", "O download da playlist foi cancelado pelo usuário.")

    def download_error(self, error):
        self.log_message(f"Erro: {error}"); QMessageBox.critical(self, "Erro", error)

    def log_message(self, message):
        from datetime import datetime
        self.status_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
