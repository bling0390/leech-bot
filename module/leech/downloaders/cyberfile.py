import re
import httpx
import datetime
import functools
from bs4 import BeautifulSoup
from tool.utils import get_redis_unique_key
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.downloader import IDownloader
from module.leech.beans.leech_bunkr_file import LeechBunkrFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.download import check_before_download, write_file, check_after_download, move_file, \
    catch_download_exception


def get_file_info(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechBunkrFile, **kwargs) -> LeechFile:
        response = httpx.post(f'https://cyberfile.me/account/ajax/file_details', data={
            'u': int(re.findall(r'showFileInformation\((\d+)\)', httpx.get(leech_file.link).text)[0])
        }).json()

        if response['success'] and 'albumPasswordModel' not in response['html']:
            video = BeautifulSoup(response['html'], 'html.parser').select_one('video source')

            leech_file.remote_folder = response['page_url'].split('/')[-1]
            leech_file.name = response['page_title']
            leech_file.actual_link = video.get('src') if video is not None else re.findall(
                r"openUrl\('(.*)'\)",
                response['html'])[0]
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'

        return f(self, leech_file, **kwargs)

    return wrapper


class Cyberfile(IDownloader):
    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.CYBERFILE

    @catch_download_exception
    @get_file_info
    @check_before_download
    @write_file
    @check_after_download
    @move_file
    def download(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        return leech_file


instance = Cyberfile()

download_filter = instance.download_filter
download = instance.download
