import glob
import os
import sys
import time
import traceback
from pathlib import Path

import validators
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QThread
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QFrame, QApplication, QVBoxLayout, QWidget, QLabel, QFileDialog, QHBoxLayout, QSpacerItem, \
    QSizePolicy, QLayout
from qfluentwidgets import FluentIcon as FIF, SearchLineEdit, PushButton, InfoBarPosition, TitleLabel, \
    BodyLabel, StrongBodyLabel, ImageLabel, MSFluentWindow, SubtitleLabel, MessageBoxBase, ProgressBar, CaptionLabel, \
    FluentIcon, SingleDirectionScrollArea
from qfluentwidgets import NavigationItemPosition, ScrollArea, ExpandLayout, \
    PushSettingCard, SettingCardGroup, SwitchSettingCard, OptionsSettingCard, CustomColorSettingCard, HyperlinkCard, \
    PrimaryPushSettingCard, isDarkTheme, InfoBar, Theme, setTheme, setThemeColor

from config import cfg, HELP_URL, YEAR, AUTHOR, VERSION, FEEDBACK_URL
from pytube_function import PytubeFunction

APP_LOGO = str(Path(__file__).parent / "assets" / "logo.png")


def exception_hook(exctype, value, tb):
    print('Unhandled Exception:', exctype, value)
    print(''.join(traceback.format_exception(exctype, value, tb)))

    # Code to run when the app crashes
    download_dir = str(Path(__file__).parent / "assets" / "downloads")
    files_to_remove = glob.glob(f'{download_dir}/*')
    for file in files_to_remove:
        os.remove(file)


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class PlayListDownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    complete_signal = pyqtSignal(int)
    all_done_signal = pyqtSignal(bool)

    def __init__(self, urls: list):
        super().__init__()
        self.urls = urls
        self.total_complete = 0

    def run(self):
        for url in self.urls:
            downloader = PytubeFunction(cfg.get(cfg.downloadFolder))
            downloader.download_video(url, self.on_progress_callback, self.on_complete_callback, self.all_done_callback)
        self.all_done_signal.emit(True)

    def on_progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = int(bytes_downloaded / total_size * 100)
        self.progress_signal.emit(percentage_of_completion)

    def on_complete_callback(self, stream, file_path):
        pass

    def all_done_callback(self):
        self.total_complete += 1
        self.complete_signal.emit(self.total_complete)


class PlayListSearchThread(QThread):
    signal = pyqtSignal(dict)

    def __init__(self, parent, url):
        super().__init__()
        self.parent = parent
        self.url = url

    def run(self):
        playlist_detail = PytubeFunction(cfg.get(cfg.downloadFolder))
        get_detail = playlist_detail.search_playlist(self.url)
        self.signal.emit(get_detail)


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
        self.download_thread = PlayListDownloadThread(self.urls)
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
            InfoBar.success("Success", "Your video downloaded successfully.", duration=15000, parent=self.parent,
                            position=InfoBarPosition.BOTTOM_RIGHT)
        else:
            InfoBar.error("Error", "An error occurred, please try again!", duration=15000, parent=self.parent,
                          position=InfoBarPosition.BOTTOM_RIGHT)

    def keyPressEvent(self, event):
        event.ignore()


class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    timeleft_signal = pyqtSignal(str)
    all_done_signal = pyqtSignal(bool)

    def __init__(self, url: str, download_as):
        super().__init__()
        self.url = url
        self.download_as = download_as

        self.start_time = time.time()

    def run(self):
        downloader = PytubeFunction(cfg.get(cfg.downloadFolder))
        if self.download_as == "audio":
            downloader.download_audio(self.url, self.on_progress_callback, self.on_complete_callback,
                                      self.all_done_callback)
        else:
            downloader.download_video(self.url, self.on_progress_callback, self.on_complete_callback,
                                      self.all_done_callback)

    def on_progress_callback(self, stream, _, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = int(bytes_downloaded / total_size * 100)

        elapsed_time = time.time() - self.start_time
        download_speed = bytes_downloaded / elapsed_time
        estimated_time_left = int(bytes_remaining / download_speed)

        self.progress_signal.emit(percentage_of_completion)
        self.timeleft_signal.emit(f'Estimated time left: {self.format_time(estimated_time_left)}')

    def on_complete_callback(self, _, file_path):
        self.timeleft_signal.emit(f'Processing file: {file_path}')

    def all_done_callback(self, ):
        self.all_done_signal.emit(True)

    @staticmethod
    def format_time(seconds: int) -> str:
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "%02d:%02d:%02d" % (hours, minutes, seconds)


class QuickSearchThread(QThread):
    signal = pyqtSignal(dict)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        video_detail = PytubeFunction(cfg.get(cfg.downloadFolder))
        get_detail = video_detail.quick_search(self.url)
        self.signal.emit(get_detail)


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
        self.hideYesButton()
        self.cancelButton.setText("Close")
        self.widget.setMinimumSize(*self.MINIMUM_SIZE)
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
            InfoBar.success("Success", f"Your {self.download_as.capitalize()} downloaded successfully.", duration=15000,
                            parent=self.parent,
                            position=InfoBarPosition.BOTTOM_RIGHT)
        else:
            InfoBar.error("Error", "An error occurred, please try again!", duration=15000, parent=self.parent,
                          position=InfoBarPosition.BOTTOM_RIGHT)

        self.clearFocus()
        self.close()

    def keyPressEvent(self, event):
        event.ignore()


class PlayListCardWidget(QWidget):
    def __init__(self, parent, playlist_info: dict):
        super().__init__(parent)
        self.setObjectName("playlist_card")

        self.parent = parent

        self.p_title = playlist_info["title"]
        self.p_videos = playlist_info["videos"]
        self.p_views = playlist_info["views"]
        self.p_last_updated = playlist_info["last_updated"]
        self.p_owner = playlist_info["owner"]

        self.p_video_info = playlist_info["video_info"]
        self.p_video_urls = playlist_info["video_urls"]

        self.first_image = self.p_video_info[0]["thumbnail_path"]

        self.init_ui()

    def init_ui(self):
        self._init_main_layout()
        self._init_left_layout()
        self._init_scroll_area()

    def _init_main_layout(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setAlignment(Qt.AlignAbsolute)

    def _init_left_layout(self):
        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setAlignment(Qt.AlignTop)

        self.add_widgets_to_left_layout()

        self.main_layout.addLayout(self.left_layout)

    def add_widgets_to_left_layout(self):
        self._add_playlist_image()
        self._add_labels()
        self._add_download_all_button()

    def _add_playlist_image(self):
        self.playlist_image = ImageLabel(image=self.first_image)
        self.playlist_image.scaledToHeight(200)
        self.playlist_image.setBorderRadius(5, 5, 5, 5)
        self.left_layout.addWidget(self.playlist_image)

    def _add_labels(self):
        self.label_1 = TitleLabel(text=self.p_title)
        self.left_layout.addWidget(self.label_1)

        self.label_2 = StrongBodyLabel(text=self.p_owner)
        self.left_layout.addWidget(self.label_2)

        self.label_3 = CaptionLabel(text=f"{self.p_videos}, {self.p_views}, {self.p_last_updated}")
        self.left_layout.addWidget(self.label_3)

    def _add_download_all_button(self):
        self.download_all_btn = PushButton(text="Download all", icon=FluentIcon.DOWNLOAD)
        self.download_all_btn.clicked.connect(self.download_all_callback)
        self.left_layout.addWidget(self.download_all_btn)

    def _init_scroll_area(self):
        self.scrollArea = SingleDirectionScrollArea(orient=Qt.Vertical)

        self.view = QWidget()
        self.layout = QVBoxLayout(self.view)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.add_video_widgets()

        self.scrollArea.setWidget(self.view)
        self.scrollArea.setStyleSheet("QScrollArea{background: transparent; border: none}")
        self.view.setStyleSheet("QWidget{background: transparent}")

        self.main_layout.addWidget(self.scrollArea)

    def add_video_widgets(self):
        for video in self.p_video_info:
            self._add_video_widget(video['thumbnail_path'], video['title'], video['views'], video['publish_date'])

    def _add_video_widget(self, thumbnail_path: str, title: str, views: str, publish_date: str) -> None:
        self.right_layout = QHBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setAlignment(Qt.AlignTop)

        self.video_image = ImageLabel(image=thumbnail_path)
        self.video_image.scaledToHeight(100)
        self.video_image.setBorderRadius(5, 5, 5, 5)
        self.right_layout.addWidget(self.video_image)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.setContentsMargins(10, 0, 0, 0)
        self.vertical_layout.setAlignment(Qt.AlignTop)

        self.label_4 = StrongBodyLabel(text=title)
        self.vertical_layout.addWidget(self.label_4)

        self.label_5 = CaptionLabel(text=f"{self.p_owner}, {views}, {publish_date}")
        self.vertical_layout.addWidget(self.label_5)

        self.right_layout.addLayout(self.vertical_layout)

        self.layout.addLayout(self.right_layout)

    def download_all_callback(self):
        dialog = PlayListDownloadDialog(self.parent, self.p_video_urls)
        dialog.exec()


class PlayListInterFace(QFrame):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setObjectName("playlist_interface")

        self.parent = parent

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.setLayout(self.main_layout)

        self._init_layout()

    def _init_widgets(self) -> None:
        # Create Widgets
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("Paste URL")
        self.search_input.searchSignal.connect(lambda text: self._search_callback(text))

        self.refresh_btn = PushButton(text="Refresh", icon=FIF.SYNC)
        self.refresh_btn.clicked.connect(self.refresh_callback)

        # Add Widgets
        self.top_layout.addWidget(self.search_input)
        self.top_layout.addWidget(self.refresh_btn)

    def _init_layout(self) -> None:
        # Create Layouts
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(10, 10, 10, 10)
        self.top_layout.setAlignment(Qt.AlignTop)

        self.view_layout = QHBoxLayout()
        self.view_layout.setContentsMargins(40, 10, 40, 10)
        self.view_layout.setAlignment(Qt.AlignTop)

        # Add Layouts
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.view_layout)

        self._init_widgets()

    def _preview_ui(self, playlist_info: dict) -> None:
        if playlist_info:
            playlist_card = PlayListCardWidget(self.parent, playlist_info)
            self.view_layout.addWidget(playlist_card)

    def _search_callback(self, url: str) -> None:
        if self.validate_url(url):
            self.url = url
            self.search_input.setDisabled(True)

            self.playlist_quick_search = PlayListSearchThread(self.parent, self.url)
            self.playlist_quick_search.signal.connect(self._preview_ui)
            self.playlist_quick_search.start()
        else:
            self.reset_search_input()
            self.show_warning("Invalid URL",
                              "The URL you have entered is invalid. Please check the URL and try again.")

    def refresh_callback(self) -> None:
        self.reset_search_input()
        self.clear_layout(self.view_layout)

    def download_callback(self) -> None:
        dialog = DownloadDialog(self.parent, self.url)
        dialog.exec()

    def clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
            else:
                child_layout = child.layout()
                if child_layout:
                    self.clear_layout(child_layout)

    def show_warning(self, title: str, content: str) -> None:
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self
        )

    def reset_search_input(self) -> None:
        self.search_input.setDisabled(False)
        self.search_input.clear()

    @staticmethod
    def validate_url(url: str) -> bool:
        return validators.url(url)


class InterFace(QFrame):
    def __init__(self, parent, text: str = "video"):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))

        self.parent = parent
        self.download_as = text.lower().strip()

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.setLayout(self.main_layout)

        self._init_layout()

    def _init_widgets(self) -> None:
        # Create Widgets
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("Paste URL")
        self.search_input.searchSignal.connect(lambda text: self._search_callback(text))
        # self.search_input.searchSignal.connect(self._show_loading)

        self.refresh_btn = PushButton(text="Refresh", icon=FIF.SYNC)
        self.refresh_btn.clicked.connect(self.refresh_callback)

        # Add Widgets
        self.top_layout.addWidget(self.search_input)
        self.top_layout.addWidget(self.refresh_btn)

    def _init_layout(self) -> None:
        # Create Layouts
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(10, 10, 10, 10)
        self.top_layout.setAlignment(Qt.AlignTop)

        self.view_layout = QHBoxLayout()
        self.view_layout.setContentsMargins(40, 10, 40, 10)
        self.view_layout.setAlignment(Qt.AlignTop)
        self.detail_layout = QVBoxLayout()
        self.detail_layout.setContentsMargins(10, 10, 10, 10)

        # Add Layouts
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.view_layout)

        self._init_widgets()

    def _preview_ui(self, video_info: dict) -> None:
        image = video_info["thumbnail_path"]
        title = video_info["title"]
        views = video_info["views"]
        publish_date = video_info["publish_date"]
        detail = f"{views}, {publish_date}"

        self.video_image = ImageLabel(image=image)
        self.video_image.setFixedSize(400, 200)
        self.video_image.setBorderRadius(5, 5, 5, 5)

        self.title = SubtitleLabel(text=title)
        self.title.setWordWrap(True)
        self.info = BodyLabel(text=detail)

        self.vertical_spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.view_layout.addWidget(self.video_image)

        self.detail_layout.addItem(self.vertical_spacer)
        self.detail_layout.addWidget(self.title)
        self.detail_layout.addWidget(self.info)
        self.detail_layout.addItem(self.vertical_spacer)

        self.view_layout.addLayout(self.detail_layout)

        self.download_btn = PushButton(text="Download", icon=FIF.DOWNLOAD)
        self.download_btn.setFixedSize(180, 35)
        self.download_btn.clicked.connect(self.download_callback)

        self.view_layout.addWidget(self.download_btn, Qt.AlignLeft)

    def _search_callback(self, url: str) -> None:
        if self.validate_url(url):
            self.url = url
            self.search_input.setDisabled(True)

            self.start_quick_search = QuickSearchThread(url)
            self.start_quick_search.signal.connect(self._preview_ui)
            self.start_quick_search.start()
        else:
            self.reset_search_input()
            self.show_warning("Invalid URL",
                              "The URL you have entered is invalid. Please check the URL and try again.")

    def refresh_callback(self) -> None:
        self.reset_search_input()
        self.clear_layout(self.view_layout)

    def download_callback(self) -> None:
        dialog = DownloadDialog(self.parent, self.url, self.download_as)
        dialog.exec()

    def clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
            else:
                child_layout = child.layout()
                if child_layout:
                    self.clear_layout(child_layout)

    def show_warning(self, title: str, content: str) -> None:
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self
        )

    def reset_search_input(self) -> None:
        self.search_input.setDisabled(False)
        self.search_input.clear()

    @staticmethod
    def validate_url(url: str) -> bool:
        return validators.url(url)


class GuideWidget(QWidget):
    def __init__(self, parent, step_icon: str, title: str, content: str):
        super().__init__(parent=parent)

        # Create a layout for the CardWidget
        self.card_layout = QVBoxLayout()
        # self.card_layout.setContentsMargins(20, 20, 20, 20)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Create widgets for the card
        self.step = ImageLabel(image=step_icon)
        self.step.setAlignment(Qt.AlignCenter)
        self.title = StrongBodyLabel(text=title)
        self.title.setAlignment(Qt.AlignCenter)
        self.content = BodyLabel(text=content)
        self.content.setWordWrap(True)
        self.content.setAlignment(Qt.AlignCenter)

        # Add widgets to the CardWidget's layout
        self.card_layout.addItem(self.verticalSpacer)

        self.card_layout.addWidget(self.step, alignment=Qt.AlignCenter)
        self.card_layout.addWidget(self.title, alignment=Qt.AlignCenter)
        self.card_layout.addWidget(self.content, alignment=Qt.AlignCenter)

        self.card_layout.addItem(self.verticalSpacer)

        self.setLayout(self.card_layout)

        self.setFixedWidth(400)


class HomeInterFace(QFrame):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setObjectName("home_interface")

        self._init_layout()

    def _init_layout(self):
        # Create Layouts
        self.main_layout = QVBoxLayout(self)
        self.top_layout = QVBoxLayout()
        self.guide_layout = QHBoxLayout()

        # Add Layouts
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.guide_layout)

        self.setLayout(self.main_layout)

        self._init_widgets()

    def _init_widgets(self):
        # Create Widgets
        self.app_name = TitleLabel(text="UltraFetch - YouTube Video Downloader")
        self.app_name.setContentsMargins(0, 20, 0, 0)
        self.app_name.setAlignment(Qt.AlignCenter)

        self.step_1 = GuideWidget(self, str(Path(__file__).parent / "assets" / "1.png"), "Enter the Link",
                                  "Paste your desired YouTube video URL. No fuss, just a straightforward copy-paste.")
        self.step_2 = GuideWidget(self, str(Path(__file__).parent / "assets" / "2.png"), "Preview the Video",
                                  "Watch the UI showcase your video before the download.")
        self.step_3 = GuideWidget(self, str(Path(__file__).parent / "assets" / "3.png"), "Hit Download",
                                  "One click and the video is yours. Ready for offline viewing, editing, or sharing.")

        # Add Widgets
        self.top_layout.addWidget(self.app_name)

        self.guide_layout.addWidget(self.step_1)
        self.guide_layout.addWidget(self.step_2)
        self.guide_layout.addWidget(self.step_3)


class SettingInterface(ScrollArea):
    """ Setting interface """
    downloadFolderChanged = pyqtSignal(str)
    micaEnableChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        # download folder
        self.musicInThisPCGroup = SettingCardGroup(
            self.tr("Download Folder"), self.scrollWidget)
        self.downloadFolderCard = PushSettingCard(
            self.tr('Choose folder'),
            FIF.DOWNLOAD,
            self.tr("Download directory"),
            cfg.get(cfg.downloadFolder),
            self.musicInThisPCGroup
        )

        # personalization
        self.personalGroup = SettingCardGroup(self.tr('Personalization'), self.scrollWidget)

        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.personalGroup
        )

        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('Theme color'),
            self.tr('Change the theme color of you application'),
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalGroup
        )

        # application
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('Open help page'),
            FIF.HELP,
            self.tr('Help'),
            self.tr('Discover new features and learn useful tips about UltraFetch'),
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'),
            FIF.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve UltraFetch by providing feedback'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('Check update'),
            FIF.INFO,
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + f" {VERSION}",
            self.aboutGroup
        )

        self.__initWidget()

        self.setObjectName("settings_interface")

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        self.micaCard.setEnabled(isWin11())

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(60, 63)

        # add cards to group
        self.musicInThisPCGroup.addSettingCard(self.downloadFolderCard)

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.musicInThisPCGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        style_path = str(Path(__file__).parent / "assets" / "resource" / "qss" / theme / "setting_interface.qss")
        with open(style_path, encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=5000,
            parent=self.window(),
            position=InfoBarPosition.BOTTOM_RIGHT
        )

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return

        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def __onThemeChanged(self, theme: Theme):
        """ theme changed slot """
        setTheme(theme)

        # chang the theme of setting interface
        self.__setQss()

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        cfg.themeChanged.connect(self.__onThemeChanged)

        self.downloadFolderCard.clicked.connect(
            self.__onDownloadFolderCardClicked)

        self.micaCard.checkedChanged.connect(self.micaEnableChanged)
        self.themeColorCard.colorChanged.connect(setThemeColor)

        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))


class Window(MSFluentWindow):
    """ Main Interface """

    def __init__(self):
        super().__init__()
        self._init_window()

        self.home_interface = HomeInterFace(self)
        self.video_interface = InterFace(self, 'video')
        self.audio_interface = InterFace(self, 'audio')
        self.playlist_interface = PlayListInterFace(self)
        self.settings_interface = SettingInterface(self)

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
        download_dir = str(Path(__file__).parent / "assets" / "downloads")
        files_to_remove = glob.glob(f'{download_dir}/*')
        for file in files_to_remove:
            os.remove(file)

        event.accept()


if __name__ == '__main__':
    # Define the path
    path = Path(__file__).parent / "assets" / "downloads"

    # Check if the directory exists
    if not os.path.exists(path):
        # If the directory doesn't exist, create it
        os.makedirs(path)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()
