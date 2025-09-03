import httpx
import datetime
import functools
from httpx import _status_codes

from tool.user_agents import get_random_user_agent
from module.leech.beans.leech_file import LeechFile
from config.config import WRITE_STREAM_CONNECT_TIMEOUT
from module.leech.interfaces.downloader import IDownloader
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.beans.leech_gofile_file import LeechGofileFile
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.decorators.download import catch_download_exception, check_before_download, check_after_download, \
    move_file


def write_gofile_file(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechGofileFile, **kwargs) -> LeechFile:
        if leech_file.status != LeechFileStatus.DOWNLOADING:
            return leech_file

        url = leech_file.link

        with httpx.stream(
                'GET',
                leech_file.link,
                headers={
                    'Cookie': f'accountToken={leech_file.token}',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'User-Agent': get_random_user_agent(),
                    'Accept': '*/*',
                    'Referer': url + ('/' if not url.endswith('/') else ''),
                    'Origin': url,
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'Pragma': 'no-cache',
                    'Cache-Control': 'no-cache'
                },
                timeout=WRITE_STREAM_CONNECT_TIMEOUT
        ) as response:
            if response.status_code != _status_codes.codes.OK:
                leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
                leech_file.reason = f"Couldn't download the file from {url}. Status code: {response.status_code}"
                return leech_file

            leech_file.size = int(response.headers.get('content-length'))

            with open(leech_file.get_temp_full_name(), 'wb') as handler:
                for i, chunk in enumerate(response.iter_bytes(chunk_size=4096)):
                    handler.write(chunk)

        return f(self, leech_file, **kwargs)

    return wrapper


class Gofile(IDownloader):
    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.GOFILE

    @catch_download_exception
    @check_before_download
    @write_gofile_file
    @check_after_download
    @move_file
    def download(self, leech_file: LeechGofileFile, **kwargs) -> LeechFile:
        return leech_file


instance = Gofile()

download_filter = instance.download_filter
download = instance.download
