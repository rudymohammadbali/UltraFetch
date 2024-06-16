from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLayout
from qfluentwidgets import ImageLabel, TitleLabel, StrongBodyLabel, CaptionLabel, PushButton, FluentIcon, \
    SingleDirectionScrollArea, BodyLabel, IconWidget, \
    CardWidget, SearchLineEdit, InfoBar, InfoBarPosition

from src.dialog import PlayListDownloadDialog
from src.functions import validate_url
from src.threads import QuickSearchThread


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


class GuideWidget(CardWidget):
    def __init__(self, parent, icon, title, content):
        super().__init__(parent=parent)
        self.icon_widget = IconWidget(icon)
        self.title_label = BodyLabel(title, self)
        self.content_label = CaptionLabel(content, self)

        self.h_box_layout = QHBoxLayout(self)
        self.v_box_layout = QVBoxLayout()

        self.setFixedHeight(73)
        self.icon_widget.setFixedSize(48, 48)

        self.h_box_layout.setContentsMargins(20, 11, 11, 11)
        self.h_box_layout.setSpacing(15)
        self.h_box_layout.addWidget(self.icon_widget)

        self.v_box_layout.setContentsMargins(0, 0, 0, 0)
        self.v_box_layout.setSpacing(0)
        self.v_box_layout.addWidget(self.title_label, 0, Qt.AlignVCenter)
        self.v_box_layout.addWidget(self.content_label, 0, Qt.AlignVCenter)
        self.v_box_layout.setAlignment(Qt.AlignVCenter)
        self.h_box_layout.addLayout(self.v_box_layout)


class SearchWidget(QWidget):
    def __init__(self, parent, preview_layout: QLayout, preview_ui, search: str = "video"):
        super().__init__(parent=parent)
        self.parent = parent
        self.preview_layout = preview_layout
        self.preview_ui = preview_ui
        self.url = None
        self.search = search.lower().strip()

        self.setObjectName("search_widget")
        self._init_layout()
        self._init_widget()

    def _init_layout(self) -> None:
        self.h_layout = QHBoxLayout()
        self.h_layout.setAlignment(Qt.AlignTop)

        self.setLayout(self.h_layout)

    def _init_widget(self) -> None:
        # Create Widgets
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("Paste URL")
        self.search_input.searchSignal.connect(lambda text: self._search_callback(text))

        self.refresh_btn = PushButton(text="Refresh", icon=FluentIcon.SYNC)
        self.refresh_btn.clicked.connect(self.refresh_callback)

        # Add Widgets
        self.h_layout.addWidget(self.search_input)
        self.h_layout.addWidget(self.refresh_btn)

    def _search_callback(self, url: str) -> None:
        if validate_url(url):
            self.search_input.setDisabled(True)
            self.url = url

            self.start_quick_search = QuickSearchThread(url, self.search)
            self.start_quick_search.signal.connect(self.preview_ui)
            self.start_quick_search.error_signal.connect(self.show_error)
            self.start_quick_search.start()
        else:
            self.reset_search_input()
            InfoBar.error(
                title="Invalid URL",
                content="The URL you have entered is invalid. Please check the URL and try again.",
                orient=Qt.Vertical,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=10000,
                parent=self.parent
            )

    def show_error(self, text: str) -> None:
        self.reset_search_input()
        InfoBar.error(
            title="An error occurred",
            content=text,
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=10000,
            parent=self.parent
        )

    def refresh_callback(self) -> None:
        self.reset_search_input()
        self.clear_layout(self.preview_layout)

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

    def reset_search_input(self) -> None:
        self.search_input.setDisabled(False)
        self.search_input.clear()
