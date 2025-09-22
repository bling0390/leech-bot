import yt_dlp
import datetime
import functools

from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.downloader import IDownloader
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.decorators.download import catch_download_exception


def write_ytdl_file(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        def mark_success(d):
            if d['postprocessor'] == 'MoveFiles' and d['_default_template'] == 'MoveFiles finished':
                leech_file.status = LeechFileStatus.DOWNLOAD_SUCCESS

        with yt_dlp.YoutubeDL({
            'format': 'best',
            'allow_multiple_video_streams': True,
            'allow_multiple_audio_streams': True,
            'writethumbnail': False,
            '--concurrent-fragments': 4,
            'allow_playlist_files': True,
            'overwrites': True,
            'postprocessor_hooks': [mark_success],
            'writesubtitles': 'srt',
            'extractor_args': {'subtitlesformat': 'srt'},
            'outtmpl': {'default': leech_file.get_full_name()}
        }) as ydl:
            ydl.download([leech_file.link])

        return f(self, leech_file, **kwargs)

    return wrapper


class YTDL(IDownloader):
    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.YT_DLP

    @catch_download_exception
    @write_ytdl_file
    def download(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        return leech_file


instance = YTDL()

download_filter = instance.download_filter
download = instance.download
