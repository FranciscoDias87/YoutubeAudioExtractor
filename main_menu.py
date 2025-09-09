import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QFrame, QSpacerItem, 
                             QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import QSize

def resource_path(relative_path):
    """Retorna o caminho absoluto para recursos, compatível com PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainMenuWindow(QMainWindow):
    # Sinais para comunicação entre janelas
    single_video_requested = pyqtSignal()
    playlist_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("YouTube Audio Extractor - Menu Principal")
        self.setFixedSize(800, 600)  # Tamanho fixo para melhor centralização
        
        # Centralizar na tela
        self.center_on_screen()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Espaçamento superior
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Seção do cabeçalho
        self.create_header_section(main_layout)
        
        # Espaçamento
        main_layout.addItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Seção dos botões principais
        self.create_buttons_section(main_layout)
        
        # Espaçamento
        main_layout.addItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Seção de informações
        self.create_info_section(main_layout)
        
        # Espaçamento inferior
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Aplicar estilos
        self.apply_styles()
        
    def center_on_screen(self):
        """Centralizar a janela na tela"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def create_header_section(self, main_layout):
        """Criar a seção do cabeçalho com título e logo"""
        header_layout = QVBoxLayout()
        
        # Título principal
        title_label = QLabel("YouTube Audio Extractor")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(36)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        # Subtítulo
        subtitle_label = QLabel("Extraia áudio de vídeos e playlists do YouTube com facilidade")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setObjectName("subtitleLabel")
        header_layout.addWidget(subtitle_label)
        
        main_layout.addLayout(header_layout)
        
    def create_buttons_section(self, main_layout):
        buttons_frame = QFrame()
        buttons_frame.setObjectName("buttonsFrame")
        buttons_layout = QGridLayout()
        buttons_frame.setLayout(buttons_layout)

        # Botão para vídeo único
        self.single_video_button = QPushButton()
        self.single_video_button.setObjectName("singleVideoButton")
        self.single_video_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "audio.png")))
        self.single_video_button.setIconSize(QSize(64, 64))
        self.single_video_button.setMinimumHeight(140)
        self.single_video_button.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding-top: 20px;
                font-size: 15px;
            }
            QPushButton::icon {
                position: absolute;
                top: 10px;
            }
        """)
        self.single_video_button.setText("Baixar Áudio Único\n\nExtraia áudio de um \nvídeo específico do YouTube")
        self.single_video_button.clicked.connect(self.open_single_video_window)

        # Botão para playlist
        self.playlist_button = QPushButton()
        self.playlist_button.setObjectName("playlistButton")
        self.playlist_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "playlist.png")))
        self.playlist_button.setIconSize(QSize(64, 64))
        self.playlist_button.setMinimumHeight(140)
        self.playlist_button.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding-top: 20px;
                font-size: 15px;
            }
            QPushButton::icon {
                position: absolute;
                top: 10px;
            }
        """)
        self.playlist_button.setText("Baixar Playlist\n\nBaixe todas as músicas \nde uma playlist do YouTube")
        self.playlist_button.clicked.connect(self.open_playlist_window)

        buttons_layout.addWidget(self.single_video_button, 0, 0)
        buttons_layout.addWidget(self.playlist_button, 0, 1)

        # Centralizar os botões
        buttons_container = QHBoxLayout()
        buttons_container.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        buttons_container.addWidget(buttons_frame)
        buttons_container.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addLayout(buttons_container)
        
    def create_info_section(self, main_layout):
        """Criar a seção de informações adicionais"""
        info_layout = QVBoxLayout()
        
        # Título da seção
        info_title = QLabel("Recursos Disponíveis")
        info_title.setAlignment(Qt.AlignCenter)
        info_title_font = QFont()
        info_title_font.setPointSize(16)
        info_title_font.setBold(True)
        info_title.setFont(info_title_font)
        info_title.setObjectName("infoTitle")
        info_layout.addWidget(info_title)
        
        # Lista de recursos
        features_layout = QHBoxLayout()
        
        # Coluna 1
        features_col1 = QVBoxLayout()
        features_col1.addWidget(QLabel("✓ Múltiplos formatos de áudio"))
        features_col1.addWidget(QLabel("✓ Qualidade configurável"))
        features_col1.addWidget(QLabel("✓ Nomenclatura inteligente"))
        
        # Coluna 2
        features_col2 = QVBoxLayout()
        features_col2.addWidget(QLabel("✓ Organização automática"))
        features_col2.addWidget(QLabel("✓ Interface intuitiva"))
        features_col2.addWidget(QLabel("✓ Download em lote"))
        
        features_layout.addLayout(features_col1)
        features_layout.addLayout(features_col2)
        
        # Container para centralizar as features
        features_container = QHBoxLayout()
        features_container.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        features_container.addLayout(features_layout)
        features_container.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        info_layout.addLayout(features_container)
        
        main_layout.addLayout(info_layout)
        
    def apply_styles(self):
        """Aplicar estilos CSS à janela"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8fafc, stop: 1 #e3e7ed);
            }
            
            #titleLabel {
                color: #1a237e;
                margin: 5px;
                font-size: 30px;
            }
            
            #subtitleLabel {
                color: #374151;
                margin: 5px;
                font-size: 15px;
                font-weight: bold;
            }
            
            #buttonsFrame {
                background-color: transparent;
            }
            
            #singleVideoButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                          stop: 0 #fff, stop: 1 #e3f2fd);
                border: 2px solid #1976d2;
                border-radius: 15px;
                color: #1976d2;
                margin: 10px;
                padding: 20px;
                font-weight: bold;
            }
            
            #singleVideoButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                          stop: 0 #e3f2fd, stop: 1 #bbdefb);
                color: #1565c0;
                border: 2px solid #1565c0;
                transform: translateY(-2px);
            }
            
            #singleVideoButton:pressed {
                background: #bbdefb;
                color: #0d47a1;
                border: 2px solid #0d47a1;
            }
            
            #playlistButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                          stop: 0 #fff, stop: 1 #e8f5e9);
                border: 2px solid #43a047;
                border-radius: 15px;
                color: #388e3c;
                margin: 10px;
                padding: 20px;
                font-weight: bold;
            }
            
            #playlistButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                          stop: 0 #e8f5e9, stop: 1 #c8e6c9);
                color: #2e7d32;
                border: 2px solid #2e7d32;
                transform: translateY(-2px);
            }
            
            #playlistButton:pressed {
                background: #c8e6c9;
                color: #1b5e20;
                border: 2px solid #1b5e20;
            }
            
            #infoTitle {
                color: #374151;
                margin: 15px;
            }
            
            QLabel {
                color: #374151;
                font-size: 13px;
                margin: 2px;
            }
        """)
        
    def open_single_video_window(self):
        """Emitir sinal para abrir janela de vídeo único"""
        self.single_video_requested.emit()
        
    def open_playlist_window(self):
        """Emitir sinal para abrir janela de playlist"""
        self.playlist_requested.emit()

def main():
    """Função principal para testar a tela inicial"""
    app = QApplication(sys.argv)
    
    # Definir ícone da aplicação (exibido na barra de tarefas e janela)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "icons", "logo_small.png")  # ou "icon.ico"
    app.setWindowIcon(QIcon(icon_path))
    
    window = MainMenuWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

