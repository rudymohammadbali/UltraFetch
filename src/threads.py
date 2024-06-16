import time

from PyQt5.QtCore import QThread, pyqtSignal

from src.config import cfg
from src.functions import format_time
from src.pytube_function import PytubeFunction
from src.updater import update_app


class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    timeleft_signal = pyqtSignal(str)
    all_done_signal = pyqtSignal(bool)
    # Playlist
    complete_signal = pyqtSignal(int)

    def __init__(self, url: str | list, download_as: str = "video"):
        super().__init__()
        self.url = url
        self.download_as = download_as.lower().strip()

        self.start_time = time.time()
        self.total_complete = 0

    def run(self):
        downloader = PytubeFunction(cfg.get(cfg.downloadFolder))
        if self.download_as == "audio":
            downloader.download_audio(self.url, self.on_progress_callback, self.on_complete_callback,
                                      self.all_done_callback)
        elif self.download_as == "video":
            downloader.download_video(self.url, self.on_progress_callback, self.on_complete_callback,
                                      self.all_done_callback)
        elif self.download_as == "playlist":
            for url in self.url:
                downloader.download_video(url, self.on_progress_callback, self.on_complete_callback,
                                          self.all_done_callback)
            self.all_done_signal.emit(True)

    def on_progress_callback(self, stream, _, bytes_remaining) -> None:
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = int(bytes_downloaded / total_size * 100)

        elapsed_time = time.time() - self.start_time
        download_speed = bytes_downloaded / elapsed_time
        estimated_time_left = int(bytes_remaining / download_speed)

        self.progress_signal.emit(percentage_of_completion)
        self.timeleft_signal.emit(f'Estimated time left: {format_time(estimated_time_left)}')

    def on_complete_callback(self, _, file_path) -> None:
        self.timeleft_signal.emit('Processing and merging downloaded files...')

    def all_done_callback(self, ) -> None:
        if self.download_as == "playlist":
            self.total_complete += 1
            self.complete_signal.emit(self.total_complete)
        else:
            self.all_done_signal.emit(True)


class QuickSearchThread(QThread):
    signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, url: str, search: str = "video"):
        super().__init__()
        self.url = url
        self.search = search.lower().strip()

    def run(self):
        pytube_function = PytubeFunction(cfg.get(cfg.downloadFolder))
        if self.search == "video":
            get_detail = pytube_function.quick_search(self.url)
        else:
            get_detail = pytube_function.search_playlist(self.url)

        if "error" in get_detail:
            self.error_signal.emit(get_detail["error"])
        else:
            self.signal.emit(get_detail)


class UpdateThread(QThread):
    signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

    def run(self):
        msg = update_app()
        self.signal.emit(msg)
