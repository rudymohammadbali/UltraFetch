from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import MessageBoxBase, SubtitleLabel, ProgressBar, BodyLabel, InfoBar, InfoBarPosition

from src.threads import DownloadThread


class PlayListDownloadDialog(MessageBoxBase):
    MINIMUM_SIZE = (500, 150)

    def __init__(self, parent, urls: list):
        super().__init__(parent)
        self.setObjectName("playlist_download_dialog")

        self.parent = parent
        self.urls = urls
        self.total_videos = len(urls)

        self._init_ui()
        self._init_download_thread()

    def _init_ui(self):
        self.title = SubtitleLabel(text="Downloading")
        self.progress = ProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.perc_complete = BodyLabel(text="0%")
        self.vid_completed = BodyLabel(text=f"0 Completed of {self.total_videos}")

        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.progress)
        self.h_layout.addWidget(self.perc_complete)

        self.viewLayout.addWidget(self.title)
        self.viewLayout.addLayout(self.h_layout)
        self.viewLayout.addWidget(self.vid_completed)

        self.hideYesButton()
        self.hideCancelButton()
        self.buttonGroup.hide()
        self.widget.setMinimumSize(*self.MINIMUM_SIZE)

    def _init_download_thread(self):
        self.download_thread = DownloadThread(self.urls, "playlist")
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.complete_signal.connect(self.update_completed)
        self.download_thread.all_done_signal.connect(self.close_dialog)
        self.download_thread.start()

        self.setFocus()

    def update_progress(self, value: int = None):
        if value:
            self.progress.setValue(value)
            self.perc_complete.setText(f"{value}%")

    def update_completed(self, value: int = None):
        if value:
            self.vid_completed.setText(f"{value} Complete of {self.total_videos}")
            self.progress.setValue(0)
            self.perc_complete.setText("0%")

    def close_dialog(self, value: bool = None):
        self.clearFocus()
        self.close()
        if value:
            InfoBar.success("Success", "Your videos downloaded successfully.", duration=10000, parent=self.parent,
                            position=InfoBarPosition.BOTTOM_RIGHT)
        else:
            InfoBar.error("Error", "An error occurred, please try again!", duration=10000, parent=self.parent,
                          position=InfoBarPosition.BOTTOM_RIGHT)

    def keyPressEvent(self, event):
        event.ignore()


class DownloadDialog(MessageBoxBase):
    MINIMUM_SIZE = (500, 150)

    def __init__(self, parent, url: str, download_as: str = "video"):
        super().__init__(parent)
        self.setObjectName("download_dialog")
        self.parent = parent
        self.url = url
        self.download_as = download_as

        self._init_ui()
        self._init_download_thread()

    def _init_ui(self):
        # Create Widgets
        self.title = SubtitleLabel(text="Downloading")
        self.progress = ProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.perc_complete = BodyLabel(text="0%")
        self.time_left = BodyLabel(text="Estimated time left:")

        # Create H Layout
        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.progress)
        self.h_layout.addWidget(self.perc_complete)

        # Add Widgets
        self.viewLayout.addWidget(self.title)
        self.viewLayout.addLayout(self.h_layout)
        self.viewLayout.addWidget(self.time_left)

        # Customize MessageBoxBase
        self.buttonGroup.setFixedHeight(60)
        self.buttonLayout.setContentsMargins(0, 0, 10, 0)
        self.widget.setMinimumSize(*self.MINIMUM_SIZE)
        self.hideYesButton()
        self.cancelButton.setText("Close")
        self.cancelButton.setFixedWidth(160)
        self.cancelButton.setFixedHeight(35)
        self.setFocus()

    def _init_download_thread(self):
        self.download_thread = DownloadThread(self.url, self.download_as)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.timeleft_signal.connect(self.update_timeleft)
        self.download_thread.all_done_signal.connect(self.close_dialog)
        self.download_thread.start()

    def update_progress(self, value: int = None):
        if value:
            self.progress.setValue(value)
            self.perc_complete.setText(f"{value}%")

    def update_timeleft(self, value: str = None):
        if value:
            self.time_left.setText(value)

    def close_dialog(self, value: bool = None):
        if value:
            InfoBar.success("Success", f"Your {self.download_as} downloaded successfully.", duration=10000,
                            parent=self.parent,
                            position=InfoBarPosition.BOTTOM_RIGHT)
        else:
            InfoBar.error("Error", "An error occurred, please try again!", duration=10000, parent=self.parent,
                          position=InfoBarPosition.BOTTOM_RIGHT)

        self.clearFocus()
        self.close()

    def keyPressEvent(self, event):
        event.ignore()
