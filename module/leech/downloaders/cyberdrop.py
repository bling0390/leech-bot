import json
import httpx
import datetime
import functools
from httpx import Response, _status_codes
from tool.utils import get_redis_unique_key
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.downloader import IDownloader
from module.leech.beans.leech_bunkr_file import LeechBunkrFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.decorators.download import check_before_download, check_after_download, catch_download_exception, \
    write_file, move_file


def update_file_info(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechBunkrFile, **kwargs) -> LeechBunkrFile:
        if leech_file.actual_link is None:
            actual_leech_file: LeechBunkrFile | None = get_file_info(leech_file.link)

            if actual_leech_file is None:
                return leech_file.update(
                    status=LeechFileStatus.DOWNLOAD_FAIL,
                    reason=f'Fail to get actual download url for "{leech_file.link}"',
                    updated_at=datetime.datetime.utcnow()
                )

            leech_file.actual_link = actual_leech_file.link
            leech_file.name = actual_leech_file.name
            leech_file.remote_folder = leech_file.remote_folder or actual_leech_file.name
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'

        return f(self, leech_file, **kwargs)

    return wrapper


class CyberDrop(IDownloader):

    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.CYBERDROP

    @catch_download_exception
    @update_file_info
    @check_before_download
    @write_file
    @check_after_download
    @move_file
    def download(self, leech_file: LeechBunkrFile, **kwargs) -> LeechFile:
        return leech_file


def get_file_info(link: str) -> LeechBunkrFile | None:
    try:
        response: Response = httpx.get(f'https://api.cyberdrop.me/api/file/info/{link.split("/")[-1]}')

        if response.status_code != _status_codes.codes.OK:
            return None

        file_info = json.loads(response.text)

        response: Response = httpx.get(file_info['auth_url'])

        if response.status_code != _status_codes.codes.OK:
            return None

        return LeechBunkrFile(
            link=json.loads(response.text)['url'],
            name=file_info['name']
        )
    except httpx.RequestError or Exception:
        return None


instance = CyberDrop()

download_filter = instance.download_filter
download = instance.download
