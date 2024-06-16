from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget, QLabel, QFileDialog, QHBoxLayout, QSpacerItem, \
    QSizePolicy
from qfluentwidgets import FluentIcon as FIF, PushButton, InfoBarPosition, TitleLabel, SubtitleLabel, \
    HyperlinkLabel, FluentIcon, ImageLabel, BodyLabel, InfoBarIcon, MessageBoxBase
from qfluentwidgets import ScrollArea, ExpandLayout, \
    PushSettingCard, SettingCardGroup, SwitchSettingCard, OptionsSettingCard, CustomColorSettingCard, HyperlinkCard, \
    PrimaryPushSettingCard, isDarkTheme, InfoBar, Theme, setTheme, setThemeColor

from src.config import cfg, HELP_URL, YEAR, AUTHOR, VERSION, FEEDBACK_URL
from src.dialog import DownloadDialog
from src.functions import isWin11
from src.threads import UpdateThread
from src.updater import restart_app
from src.widgets import PlayListCardWidget, GuideWidget, SearchWidget

ICONS = {
    "1": str(Path(__file__).parent / "assets" / "icons" / "1.png"),
    "2": str(Path(__file__).parent / "assets" / "icons" / "2.png"),
    "3": str(Path(__file__).parent / "assets" / "icons" / "3.png"),
}


class PlaylistInterface(QFrame):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setObjectName("playlist_interface")

        self.parent = parent

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.setLayout(self.main_layout)

        self._init_layout()

    def _init_layout(self) -> None:
        # Create Layout
        self.view_layout = QHBoxLayout()
        self.view_layout.setContentsMargins(20, 20, 20, 20)
        self.detail_layout = QVBoxLayout()
        self.detail_layout.setContentsMargins(10, 10, 10, 10)

        self.search_widget = SearchWidget(self, self.view_layout, self._preview_ui, "playlist")

        # Add Layouts
        self.main_layout.addWidget(self.search_widget)
        self.main_layout.addLayout(self.view_layout)

    def _preview_ui(self, playlist_info: dict) -> None:
        if playlist_info:
            playlist_card = PlayListCardWidget(self.parent, playlist_info)
            self.view_layout.addWidget(playlist_card)


class DownloadInterface(QWidget):
    def __init__(self, parent, text: str = "video"):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))

        self.parent = parent
        self.download_as = text.lower().strip()

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.setLayout(self.main_layout)

        self._init_layout()

    def _init_layout(self) -> None:
        # Create Layout
        self.view_layout = QHBoxLayout()
        self.view_layout.setContentsMargins(20, 20, 20, 20)
        self.detail_layout = QVBoxLayout()
        self.detail_layout.setContentsMargins(10, 10, 10, 10)

        self.search_widget = SearchWidget(self, self.view_layout, self._preview_ui, "video")

        # Add Layouts
        self.main_layout.addWidget(self.search_widget)
        self.main_layout.addLayout(self.view_layout)

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

        self.download_btn = PushButton(text=f"Download {self.download_as.capitalize()}", icon=FluentIcon.DOWNLOAD)
        self.download_btn.setFixedSize(180, 35)
        self.download_btn.clicked.connect(self.download_callback)

        self.view_layout.addWidget(self.download_btn, Qt.AlignLeft)

    def download_callback(self) -> None:
        url = self.search_widget.url
        dialog = DownloadDialog(self.parent, url, self.download_as)
        dialog.exec()


class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("home_interface")

        self._init_layout()

    def _init_layout(self):
        # Create Layouts
        self.main_layout = QVBoxLayout(self)
        self.top_layout = QVBoxLayout()
        self.guide_layout = QVBoxLayout()
        self.guide_layout.setContentsMargins(20, 20, 20, 20)
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(20, 20, 20, 20)
        self.bottom_layout.setSpacing(12)

        # Add Layouts
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.guide_layout)
        self.main_layout.addLayout(self.bottom_layout)

        self.setLayout(self.main_layout)

        self._init_widgets()

    def _init_widgets(self):
        # Create Widgets
        self.app_name = TitleLabel(text="UltraFetch - YouTube Video Downloader")
        self.app_name.setContentsMargins(0, 20, 0, 0)
        self.app_name.setAlignment(Qt.AlignCenter)

        verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        text = SubtitleLabel(text="How it works?")
        step_1 = GuideWidget(self, ICONS["1"], "Enter the Link",
                             "Paste your desired YouTube video URL. No fuss, just a straightforward copy-paste.")
        step_2 = GuideWidget(self, ICONS["2"], "Preview the Video",
                             "Watch the UI showcase your video before the download.")
        step_3 = GuideWidget(self, ICONS["3"], "Hit Download",
                             "One click and the video is yours. Ready for offline viewing, editing, or sharing.")

        help_url = HyperlinkLabel(QUrl(HELP_URL), 'Get help')
        help_url.setUnderlineVisible(True)

        feedback_url = HyperlinkLabel(QUrl(FEEDBACK_URL), 'Feedback')
        feedback_url.setUnderlineVisible(True)

        # Add Widgets
        self.top_layout.addWidget(self.app_name)

        self.guide_layout.addItem(verticalSpacer)
        self.guide_layout.addWidget(text)
        self.guide_layout.addWidget(step_1)
        self.guide_layout.addWidget(step_2)
        self.guide_layout.addWidget(step_3)
        self.guide_layout.addItem(verticalSpacer)

        self.bottom_layout.addWidget(help_url)
        self.bottom_layout.addWidget(feedback_url, Qt.AlignLeft)


class SettingInterface(ScrollArea):
    mica_enable_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.parent = parent

        self.scroll_widget = QWidget()
        self.expand_layout = ExpandLayout(self.scroll_widget)
        self.setting_label = QLabel(self.tr("Settings"), self)

        self.folder_group = SettingCardGroup(
            self.tr("Download Folder"), self.scroll_widget)

        self.download_folder_card = PushSettingCard(
            self.tr('Choose folder'),
            FIF.DOWNLOAD,
            self.tr("Download directory"),
            cfg.get(cfg.downloadFolder),
            self.folder_group
        )

        self.personal_group = SettingCardGroup(self.tr('Personalization'), self.scroll_widget)

        self.mica_card = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.personal_group
        )

        self.theme_card = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personal_group
        )
        self.theme_color_card = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('Theme color'),
            self.tr('Change the theme color of you application'),
            self.personal_group
        )

        self.about_group = SettingCardGroup(self.tr('About'), self.scroll_widget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('Open help page'),
            FIF.HELP,
            self.tr('Help'),
            self.tr('Discover new features and learn useful tips about UltraFetch'),
            self.about_group
        )
        self.feedback_card = PrimaryPushSettingCard(
            self.tr('Provide feedback'),
            FIF.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve UltraFetch by providing feedback'),
            self.about_group
        )
        self.about_card = PrimaryPushSettingCard(
            self.tr('Check update'),
            FIF.INFO,
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + f" {VERSION}",
            self.about_group
        )

        self.__init_widget()

        self.setObjectName("settings_interface")

    def __init_widget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__set_qss()
        self.mica_card.setEnabled(isWin11())

        # initialize layout
        self.__init_layout()
        self.__connect_signal_to_slot()

    def __init_layout(self):
        self.setting_label.move(60, 63)

        # add cards to group
        self.folder_group.addSettingCard(self.download_folder_card)

        self.personal_group.addSettingCard(self.mica_card)
        self.personal_group.addSettingCard(self.theme_card)
        self.personal_group.addSettingCard(self.theme_color_card)

        self.about_group.addSettingCard(self.helpCard)
        self.about_group.addSettingCard(self.feedback_card)
        self.about_group.addSettingCard(self.about_card)

        # add setting card group to layout
        self.expand_layout.setSpacing(28)
        self.expand_layout.setContentsMargins(60, 10, 60, 0)
        self.expand_layout.addWidget(self.folder_group)
        self.expand_layout.addWidget(self.personal_group)
        self.expand_layout.addWidget(self.about_group)

    def __set_qss(self):
        self.scroll_widget.setObjectName('scrollWidget')
        self.setting_label.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        style_path = str(Path(__file__).parent / "assets" / "resource" / "qss" / theme / "setting_interface.qss")
        with open(style_path, encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __show_restart_tooltip(self):
        InfoBar.warning(
            self.tr('Warning'),
            self.tr('Configuration takes effect after restart'),
            duration=5000,
            parent=self.window(),
            position=InfoBarPosition.BOTTOM_RIGHT
        )

    def __on_download_folder_card_clicked(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return

        cfg.set(cfg.downloadFolder, folder)
        self.download_folder_card.setContent(folder)

    def __on_theme_changed(self, theme: Theme):
        setTheme(theme)

        # chang the theme of setting interface
        self.__set_qss()

    def __check_update(self) -> None:
        self.loading_dialog = LoadingDialog(self.parent)
        self.loading_dialog.show()
        self.update_thread = UpdateThread()
        self.update_thread.signal.connect(self.show_message)
        self.update_thread.start()

    def show_message(self, msg: bool) -> None:
        self.loading_dialog.hide()
        if msg:
            show_msg = InfoBar(
                icon=InfoBarIcon.SUCCESS,
                title='Update installed',
                content="Restart the app to complete update",
                orient=Qt.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=-1,
                parent=self
            )

            # Add custom components
            restart_btn = PushButton(text='Restart now')
            restart_btn.clicked.connect(restart_app)
            show_msg.addWidget(restart_btn)
            show_msg.show()
        else:
            show_msg = InfoBar(
                icon=InfoBarIcon.SUCCESS,
                title='No updates',
                content="You're up to date",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self
            )

            show_msg.show()

    def __connect_signal_to_slot(self):
        cfg.appRestartSig.connect(self.__show_restart_tooltip)
        cfg.themeChanged.connect(self.__on_theme_changed)

        self.download_folder_card.clicked.connect(
            self.__on_download_folder_card_clicked)

        self.mica_card.checkedChanged.connect(self.mica_enable_changed)
        self.theme_color_card.colorChanged.connect(setThemeColor)

        self.feedback_card.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))

        self.about_card.clicked.connect(self.__check_update)


class LoadingDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.viewLayout.addWidget(SubtitleLabel(text="Update available"))
        self.viewLayout.addWidget(BodyLabel(text="Please wait while installing new update."))

        self.widget.setMinimumWidth(400)
        self.buttonGroup.hide()
