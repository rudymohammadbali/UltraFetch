import glob
import os
import sys
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF, MSFluentWindow
from qfluentwidgets import NavigationItemPosition

from src.config import cfg
from src.interfaces import HomeInterface, PlaylistInterface, SettingInterface, DownloadInterface

APP_LOGO = str(Path(__file__).parent / "src" / "assets" / "icons" / "logo.png")


class Window(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self._init_window()

        self.download_dir = Path(__file__).parent / "src" / "assets" / "downloads"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        self.home_interface = HomeInterface(self)
        self.video_interface = DownloadInterface(self, 'video')
        self.audio_interface = DownloadInterface(self, 'audio')
        self.playlist_interface = PlaylistInterface(self)
        self.settings_interface = SettingInterface(self)

        self.settings_interface.mica_enable_changed.connect(self.setMicaEffectEnabled)

        self.init_navigation()

    def init_navigation(self):
        self.addSubInterface(self.home_interface, FIF.HOME, 'Home')
        self.addSubInterface(self.video_interface, FIF.VIDEO, 'Video')
        self.addSubInterface(self.audio_interface, FIF.MUSIC, 'MP3')
        self.addSubInterface(self.playlist_interface, FIF.MEDIA, 'Playlist')

        self.addSubInterface(self.settings_interface, FIF.SETTING, 'Settings', position=NavigationItemPosition.BOTTOM)

    def _init_window(self):
        self.resize(1280, 720)
        self.setWindowIcon(QIcon(APP_LOGO))
        self.setWindowTitle('UltraFetch')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # Center window
        desktop = QApplication.desktop().availableGeometry()
        width, height = desktop.width(), desktop.height()
        self.move(width // 2 - self.width() // 2, height // 2 - self.height() // 2)

    def closeEvent(self, event):
        files_to_remove = glob.glob(f'{self.download_dir}/*')
        for file in files_to_remove:
            os.remove(file)

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
