from pathlib import Path

from qfluentwidgets import (qconfig, QConfig, ConfigItem, FolderValidator,
                            BoolValidator, Theme)

from src.functions import isWin11

downloads_path = Path.home() / 'Downloads'


class Config(QConfig):
    """ Config of application """

    # download folders
    downloadFolder = ConfigItem(
        "Folders", "Download", str(downloads_path), FolderValidator())

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())


YEAR = 2024
AUTHOR = "rudymohammadbali"
VERSION = "1.1.2"
HELP_URL = "https://github.com/rudymohammadbali/UltraFetch/discussions/categories/q-a"
FEEDBACK_URL = "https://github.com/rudymohammadbali/UltraFetch/issues"
RELEASE_URL = "https://github.com/rudymohammadbali/UltraFetch/releases/latest"

cfg = Config()
cfg.themeMode.value = Theme.AUTO
cfg.micaEnabled.value = False
cfg.themeColor.value = "#ffaa0000"
qconfig.load(Path(__file__).parent / "config" / "config.json", cfg)
