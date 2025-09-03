import httpx
import datetime
import functools
from loguru import logger
from httpx import _status_codes

from tool.utils import get_redis_unique_key
from tool.user_agents import get_random_user_agent
from module.leech.beans.leech_file import LeechFile
from module.leech.utils.bunkr import parse_bunkr_link
from module.leech.interfaces.downloader import IDownloader
from module.leech.beans.leech_bunkr_file import LeechBunkrFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.constants.leech_file_status import LeechFileStatus
from config.config import WRITE_STREAM_CONNECT_TIMEOUT, BOT_DOWNLOAD_LOCATION, BUNKR_DOMAIN
from module.leech.decorators.download import check_before_download, check_after_download, catch_download_exception, \
    move_file


def get_bunkr_actual_link(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechBunkrFile, **kwargs) -> LeechBunkrFile:
        if leech_file.actual_link is None:
            leech_files: list[LeechBunkrFile] = parse_link(leech_file.link)

            if len(leech_files) == 0 or leech_files[0] is None:
                leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
                leech_file.reason = f'Fail to get actual download url for "{leech_file.link}"'
                return leech_file

            leech_file.actual_link = leech_files[0].actual_link
            leech_file.name = leech_files[0].name
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'

        return f(self, leech_file, **kwargs)

    return wrapper


def write_bunkr_file(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechBunkrFile, **kwargs) -> LeechBunkrFile:
        if leech_file.status != LeechFileStatus.DOWNLOADING:
            return leech_file

        with httpx.stream(
            'get',
            leech_file.actual_link,
            headers={
                'User-Agent': get_random_user_agent(),
                'Referer': f'https://{BUNKR_DOMAIN}',
                'Range': 'bytes=0-'
            },
            timeout=WRITE_STREAM_CONNECT_TIMEOUT
        ) as r:
            if r.status_code not in [_status_codes.codes.OK, _status_codes.codes.PARTIAL_CONTENT]:
                leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
                leech_file.reason = f"Error downloading \"{leech_file.name}\": {r.status_code}."
                return leech_file

            if r.url == "https://bnkr.b-cdn.net/maintenance.mp4":
                leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
                leech_file.reason = f"Error downloading \"{leech_file.name}\": Server is down for maintenance."
                return leech_file

            leech_file.size = int(r.headers.get('content-length', -1))

            with open(leech_file.get_temp_full_name(), 'wb') as file:
                for chunk in r.iter_bytes(chunk_size=8192):
                    if chunk is not None:
                        file.write(chunk)

        return f(self, leech_file, **kwargs)

    return wrapper


def parse_link(link: str, **kwargs) -> list[LeechBunkrFile]:
    try:
        return parse_bunkr_link(link, **kwargs)
    except Exception as e:
        logger.error(f'Error parse link {link}: {str(e)}')

    return []


class Bunkr(IDownloader):
    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.BUNKR

    @catch_download_exception
    @get_bunkr_actual_link
    @check_before_download
    @write_bunkr_file
    @check_after_download
    @move_file
    def download(self, leech_file: LeechBunkrFile, **kwargs) -> LeechBunkrFile:
        return leech_file


instance = Bunkr()

download_filter = instance.download_filter
download = instance.download
