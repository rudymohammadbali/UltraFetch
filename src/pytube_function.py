import os
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Union, List

import requests
from pytube import YouTube, Playlist

from src.functions import validate_url


def remove_file(path: str) -> None:
    try:
        if os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass


def remove_files(paths: Union[str, List[str]]) -> None:
    try:
        if isinstance(paths, list):
            for path in paths:
                remove_file(path)
        else:
            remove_file(paths)
    except Exception:
        pass


def format_publish_date(publish_date: datetime) -> str:
    current_date = datetime.now()

    diff = current_date - publish_date
    days_diff = diff.days
    hours_diff = diff.total_seconds() // 3600

    if hours_diff < 24:
        return f"{hours_diff} hours ago"
    elif days_diff < 30:
        return f"{days_diff} days ago"

    years_diff = current_date.year - publish_date.year
    months_diff = current_date.month - publish_date.month

    total_months_diff = years_diff * 12 + months_diff

    if total_months_diff > 12:
        years = total_months_diff // 12
        return f"{years} years ago"
    else:
        return f"{total_months_diff} months ago"


def format_view_count(views: int) -> str:
    suffixes = {6: 'M', 3: 'K', 0: ''}
    for power, suffix in sorted(suffixes.items(), reverse=True):
        if views >= 10 ** power:
            views /= 10 ** power
            return f'{views:.1f}{suffix} views'
    return f'{views} views'


def rename_title(title: str) -> str:
    title = re.sub(r'[\\/*?:"<>|.]', '', title).strip()
    title = title.replace(" ", "_")
    return title


class PytubeFunction:
    CREATION_FLAGS = 0x08000000  # hides ffmpeg console

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.download_path = Path(__file__).parent / "assets" / "downloads"

    def download_thumbnail(self, thumbnail_url: str) -> str:
        if validate_url(thumbnail_url):
            response = requests.get(thumbnail_url)

            if response.status_code == 200:
                rand_filename = str(uuid.uuid4()) + '.jpg'
                output = self.download_path / rand_filename
                with open(output, 'wb') as file:
                    file.write(response.content)
                return str(output)

    def download_audio(self, url: str, progress_callback: any, complete_callback: any,
                       all_complete_callback: any) -> None:
        try:
            if validate_url(url):
                yt_obj = YouTube(url, progress_callback, complete_callback)

                video_title = yt_obj.title
                title = rename_title(video_title)
                output_file = Path(self.output_dir) / f"{title}.mp3"

                audio_stream = yt_obj.streams.filter(only_audio=True).order_by('abr').desc().first()

                audio_path = audio_stream.download(output_path=str(self.download_path), filename='audio')

                subprocess.run(['ffmpeg', '-y', '-i', audio_path, '-c:a', 'libmp3lame', output_file],
                               creationflags=self.CREATION_FLAGS)

                # Clean up temp files
                remove_files(str(audio_path))

                # Process complete
                all_complete_callback()
        except Exception as e:
            print(f"An error occurred: {e}")

    def download_video(self, url: str, progress_callback: any, complete_callback: any,
                       all_complete_callback: any) -> None:
        if validate_url(url):
            yt_obj = YouTube(url, progress_callback, complete_callback)

            video_title = yt_obj.title
            title = rename_title(video_title)
            output_file = Path(self.output_dir) / f"{title}.mp4"

            video_stream = yt_obj.streams.filter(progressive=False, adaptive=True).order_by(
                'resolution').desc().first()
            audio_stream = yt_obj.streams.filter(only_audio=True).order_by('abr').desc().first()

            video_path = video_stream.download(output_path=str(self.download_path), filename='video')
            audio_path = audio_stream.download(output_path=str(self.download_path), filename='audio')

            video = self.download_path / "video.mp4"
            audio = self.download_path / "audio.mp3"

            subprocess.run(['ffmpeg', '-y', '-i', video_path, '-c:v', 'copy', video], creationflags=self.CREATION_FLAGS)
            subprocess.run(['ffmpeg', '-y', '-i', audio_path, '-c:a', 'libmp3lame', audio],
                           creationflags=self.CREATION_FLAGS)
            subprocess.run(['ffmpeg', '-y', '-i', video, '-i', audio, '-c:v', 'copy', '-c:a', 'aac', output_file],
                           creationflags=self.CREATION_FLAGS)

            # Clean up temp files
            remove_files([str(audio), str(audio_path), str(video), str(video_path)])

            # Process complete
            all_complete_callback()

    def search_playlist(self, url: str):
        try:
            if validate_url(url):
                p = Playlist(url)
                title = p.title
                owner = p.owner
                videos = f"{p.length} videos"
                views = format_view_count(p.views)
                d = p.last_updated
                if isinstance(d, str):
                    updated = "N/A"
                else:
                    dt = datetime.combine(d, datetime.min.time())
                    updated = format_publish_date(dt)

                video_details = []
                video_urls = []

                for video_url in p.video_urls:
                    video_urls.append(video_url)
                    video_detail = self.quick_search(video_url)
                    video_details.append(video_detail)

                return {"title": title, "owner": owner, "videos": videos, "views": views, "last_updated": updated,
                        "video_info": video_details, "video_urls": video_urls}
        except Exception as e:
            return {"error": str(e)}

    def quick_search(self, url: str) -> dict:
        try:
            if validate_url(url):
                yt_obj = YouTube(url)
                title = yt_obj.title
                owner = yt_obj.author
                channel_url = yt_obj.channel_url
                thumbnail_url = yt_obj.thumbnail_url
                thumbnail_path = self.download_thumbnail(thumbnail_url)
                views = format_view_count(yt_obj.views)
                publish_date = format_publish_date(yt_obj.publish_date)

                return {"title": title, "owner": owner, "channel_url": channel_url, "thumbnail_url": thumbnail_url,
                        "thumbnail_path": thumbnail_path,
                        "views": views,
                        "publish_date": publish_date}
        except Exception as e:
            return {"error": str(e)}
