import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytube
import requests

DOWNLOAD_PATH = Path(__file__).parent / "assets" / "downloads"


def update_app() -> bool:
    # Get the current version of the app
    current_version = get_current_version()

    # Get the latest version from GitHub
    latest_version = get_latest_version_from_github()

    # Compare the current version with the latest version
    if current_version != latest_version:
        # If an update is available, fetch the update
        fetch_update_from_github()
        return True
    else:
        return False


def get_current_version() -> str:
    return pytube.__version__


def get_latest_version_from_github() -> str:
    url = "https://raw.githubusercontent.com/pytube/pytube/master/pytube/version.py"
    response = requests.get(url)

    # The content of the file is included in the response text
    file_content = response.text
    version = None

    # Split the content by lines and iterate over them
    for line in file_content.split('\n'):
        # Check if the line starts with '__version__'
        if line.startswith('__version__'):
            # Split the line by equals sign and get the second part (the version number)
            version = line.split('=')[1].strip().strip('"')
            break

    return version


def copy_and_replace(source_dir, target_dir) -> None:
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)

    pytube_dir = str(DOWNLOAD_PATH / "pytube")
    if os.path.exists(pytube_dir):
        os.chdir(str(DOWNLOAD_PATH))
        try:
            os.system(f"rmdir /s /q {pytube_dir}")
        except Exception as e:
            print(e)


def fetch_update_from_github():
    command = ["git", "clone", "https://github.com/pytube/pytube.git"]
    os.chdir(str(DOWNLOAD_PATH))
    subprocess.run(command, creationflags=0x08000000)

    # Specify the source and target directories
    source_dir = str(DOWNLOAD_PATH / "pytube" / "pytube")
    target_dir = sys.modules['pytube'].__path__
    # Call the function
    copy_and_replace(source_dir, target_dir[0])


def restart_app():
    os.execl(sys.executable, sys.executable, *sys.argv)
