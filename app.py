import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from main_menu import MainMenuWindow
from single_video_window import SingleVideoWindow
from playlist_window import PlaylistWindow
from splash_screen import SplashScreen

class YouTubeAudioExtractorApp(QObject):
    """Classe principal que gerencia todas as janelas da aplicação"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar splash screen primeiro
        self.splash = SplashScreen()
        
        # Inicializar janelas
        self.main_menu = MainMenuWindow()
        self.single_video_window = SingleVideoWindow()
        self.playlist_window = PlaylistWindow()
        
        # Conectar sinais do menu principal
        self.main_menu.single_video_requested.connect(self.show_single_video_window)
        self.main_menu.playlist_requested.connect(self.show_playlist_window)
        
        # Conectar sinais de volta ao menu
        self.single_video_window.back_to_menu_requested.connect(self.show_main_menu)
        self.playlist_window.back_to_menu_requested.connect(self.show_main_menu)
        
        # Configurar fechamento da aplicação
        self.main_menu.closeEvent = self.close_application
        self.single_video_window.closeEvent = self.close_application
        self.playlist_window.closeEvent = self.close_application
        
    def show_main_menu(self):
        """Mostrar o menu principal e esconder outras janelas"""
        self.single_video_window.hide()
        self.playlist_window.hide()
        self.main_menu.show()
        self.main_menu.raise_()
        self.main_menu.activateWindow()
        
    def show_single_video_window(self):
        """Mostrar janela de vídeo único e esconder outras"""
        self.main_menu.hide()
        self.playlist_window.hide()
        self.single_video_window.show()
        self.single_video_window.raise_()
        self.single_video_window.activateWindow()
        
    def show_playlist_window(self):
        """Mostrar janela de playlist e esconder outras"""
        self.main_menu.hide()
        self.single_video_window.hide()
        self.playlist_window.show()
        self.playlist_window.raise_()
        self.playlist_window.activateWindow()
        
    def close_application(self, event):
        """Fechar toda a aplicação quando qualquer janela for fechada"""
        # Fechar todas as janelas
        self.main_menu.close()
        self.single_video_window.close()
        self.playlist_window.close()
        
        # Aceitar o evento de fechamento
        event.accept()
        
        # Sair da aplicação
        QApplication.quit()
        
    def run(self):
        """Iniciar a aplicação mostrando primeiro a splash screen"""
        # Mostrar splash screen
        self.splash.show()
        self.splash.start_loading()
        
        # Timer para fechar splash e mostrar menu principal
        QTimer.singleShot(3000, self.show_main_menu_after_splash)
        
    def show_main_menu_after_splash(self):
        """Mostrar menu principal após splash screen"""
        self.splash.close()
        self.show_main_menu()

def main():
    """Função principal da aplicação"""
    # Criar aplicação Qt
    app = QApplication(sys.argv)
    
    # Configurar propriedades da aplicação
    app.setApplicationName("YouTube Audio Extractor")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Francisco Dias")
    
    # Configurar estilo global da aplicação
    app.setStyleSheet("""
        QApplication {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QMainWindow {
            background-color: #ffffff;
        }
        
        QWidget {
            font-size: 11px;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: #fafafa;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            color: #2c3e50;
            background-color: #ffffff;
        }
        
        QLineEdit {
            border: 2px solid #ddd;
            border-radius: 6px;
            padding: 8px;
            font-size: 12px;
            background-color: #ffffff;
        }
        
        QLineEdit:focus {
            border-color: #4CAF50;
            background-color: #f8fff8;
        }
        
        QPushButton {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #e9ecef;
            border-color: #adb5bd;
        }
        
        QPushButton:pressed {
            background-color: #dee2e6;
        }
        
        QComboBox {
            border: 1px solid #ced4da;
            border-radius: 6px;
            padding: 6px;
            font-size: 12px;
            background-color: #ffffff;
        }
        
        QComboBox:focus {
            border-color: #4CAF50;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #6c757d;
            margin-right: 5px;
        }
        
        QTextEdit {
            border: 1px solid #ced4da;
            border-radius: 6px;
            background-color: #f8f9fa;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
        }
        
        QProgressBar {
            border: 1px solid #ced4da;
            border-radius: 6px;
            text-align: center;
            background-color: #e9ecef;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 5px;
        }
        
        QLabel {
            color: #495057;
        }
    """)
    
    # Criar e executar aplicação
    youtube_app = YouTubeAudioExtractorApp()
    youtube_app.run()
    
    # Executar loop da aplicação
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

