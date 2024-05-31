import sys
from pathlib import Path

from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, OptionsValidator, FolderValidator,
                            BoolValidator, Theme)

downloads_path = Path.home() / 'Downloads'


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """ Config of application """

    # download folders
    downloadFolder = ConfigItem(
        "Folders", "Download", str(downloads_path), FolderValidator())

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator(), restart=True)
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)


YEAR = 2024
AUTHOR = "rudymohammadbali"
VERSION = "0.0.1"
HELP_URL = "https://github.com/rudymohammadbali/UltraFetch/discussions/categories/q-a"
FEEDBACK_URL = "https://github.com/rudymohammadbali/UltraFetch/issues"
RELEASE_URL = "https://github.com/rudymohammadbali/UltraFetch/releases/latest"

cfg = Config()
cfg.themeMode.value = Theme.AUTO
cfg.micaEnabled.value = False
qconfig.load(Path(__file__).parent / "assets" / "config" / "config.json", cfg)
