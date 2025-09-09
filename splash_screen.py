import sys
import os
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QProgressBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        
        # Configurações da janela
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)
        self.center_on_screen()
        
        # UI
        self.setup_ui()
        
        # Timer de carregamento
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.progress_value = 0

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Bloco único: logo + barra + texto
        self.container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self.container.setLayout(container_layout)

        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(__file__), "icons", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("🎵")
            font = QFont()
            font.setPointSize(80)
            self.logo_label.setFont(font)
        container_layout.addWidget(self.logo_label)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setTextVisible(False)
        container_layout.addWidget(self.progress_bar)

        # Texto de status
        self.status_label = QLabel("Carregando sistema...")
        self.status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.status_label.setFont(font)
        container_layout.addWidget(self.status_label)

        layout.addWidget(self.container)

        # Estilo geral com border-radius nos 4 cantos
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f8fafc, stop:1 #e3e7ed);
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
                border-bottom-left-radius: 15px;
                border-bottom-right-radius: 15px;
                
            }
            QProgressBar {
                border: none;
                border-radius: 0px;
                background-color: #f3f4f6;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #3b82f6, stop:1 #1d4ed8);
            }
            QLabel {
                color: #374151;
                
            }           
        """)

    def start_loading(self):
        self.timer.start(50)

    def update_progress(self):
        self.progress_value += 2
        if self.progress_value <= 100:
            self.progress_bar.setValue(self.progress_value)
            if self.progress_value < 30:
                self.status_label.setText("Carregando módulos...")
            elif self.progress_value < 60:
                self.status_label.setText("Inicializando interface...")
            elif self.progress_value < 90:
                self.status_label.setText("Preparando sistema...")
            else:
                self.status_label.setText("Quase pronto...")
        else:
            self.timer.stop()
            self.status_label.setText("Sistema carregado!")
            QTimer.singleShot(500, self.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    splash.start_loading()
    sys.exit(app.exec_())
