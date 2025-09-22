from loguru import logger
from mega import Mega as MegaTools

from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.downloader import IDownloader
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.download import check_before_download
from module.leech.constants.leech_file_status import LeechFileStatus
from config.config import MEGA_AUTHORIZATION_EMAIL, MEGA_AUTHORIZATION_PASSWORD


class Mega(IDownloader):
    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.MEGA

    def __init__(self):
        try:
            self.instance = MegaTools().login(email=MEGA_AUTHORIZATION_EMAIL, password=MEGA_AUTHORIZATION_PASSWORD)
        except Exception as e:
            logger.error(e)

    @check_before_download
    def download(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        try:
            self.instance.download_url(leech_file.link, dest_path=leech_file.location, dest_filename=leech_file.name)
            leech_file.status = LeechFileStatus.DOWNLOAD_SUCCESS
        except Exception as e:
            leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
            leech_file.reason = str(e)
            logger.info(e)

        return leech_file


instance = Mega()

download_filter = instance.download_filter
download = instance.download
