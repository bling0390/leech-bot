import re
import httpx
import gdown
import datetime
import functools
from httpx import _status_codes
from tool.utils import get_redis_unique_key
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.downloader import IDownloader
from module.leech.beans.leech_bunkr_file import LeechBunkrFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.download import check_before_download, check_after_download, move_file, \
    catch_download_exception, write_file

ID_PATTERNS = [
    re.compile("/file/d/([0-9A-Za-z_-]{10,})(?:/|$)", re.IGNORECASE),
    re.compile("/folders/([0-9A-Za-z_-]{10,})(?:/|$)", re.IGNORECASE),
    re.compile("id=([0-9A-Za-z_-]{10,})(?:&|$)", re.IGNORECASE),
    re.compile("([0-9A-Za-z_-]{10,})", re.IGNORECASE),
]


def get_file_info(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechBunkrFile, **kwargs) -> LeechFile:
        response = httpx.head(leech_file.actual_link)

        if response.status_code == _status_codes.codes.OK:
            name = re.findall(r'filename="(.*)"', response.headers.get('Content-Disposition'))[0]

            leech_file.remote_folder = name
            leech_file.name = name
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'

        return f(self, leech_file, **kwargs)

    return wrapper


class GD(IDownloader):
    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.GD

    @catch_download_exception
    @get_file_info
    @check_before_download
    @write_file
    @check_after_download
    @move_file
    def download(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        return leech_file


instance = GD()

download_filter = instance.download_filter
download = instance.download
