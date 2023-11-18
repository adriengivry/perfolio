import qdarktheme

from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtGui import QIcon, QAction

from perfolio.gui import MainWindow
from perfolio.settings import AppSettings
from perfolio.utils import Utils

class Application:
    def __init__(self, argv:list[str]):
        # Create application
        self.app = QApplication(argv)
        
        # Setup environment
        AppSettings.load_settings()
        
        qdarktheme.setup_theme(AppSettings.get("theme"))

        # Create window
        self.main_window = MainWindow()
        screen_geometry = self.app.primaryScreen().availableGeometry()
        main_window_width = 1280
        main_window_height = 960
        self.main_window.setGeometry(
            (screen_geometry.width() - main_window_width) // 2,
            (screen_geometry.height() - main_window_height) // 2,
            main_window_width,
            main_window_height
        )
        self.main_window.show()
        
    def run(self) -> bool:
        return self.app.exec()