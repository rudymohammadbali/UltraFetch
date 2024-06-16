import glob
import os
import sys
import traceback
from pathlib import Path

import validators


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


def validate_url(url: str) -> bool:
    return validators.url(url)


def format_time(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)
