from loguru import logger
from mega import Mega as MegaTools

from tool.utils import get_redis_unique_key
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document
from config.config import BOT_DOWNLOAD_LOCATION, MEGA_AUTHORIZATION_EMAIL, MEGA_AUTHORIZATION_PASSWORD


class Mega(IParser):
    def __init__(self):
        try:
            self.instance = MegaTools().login(email=MEGA_AUTHORIZATION_EMAIL, password=MEGA_AUTHORIZATION_PASSWORD)
        except Exception as e:
            logger.error(e)

    def parse_link_filter(self, link: str) -> bool:
        return 'mega.nz' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files = []

        if '/file/' in link:
            file_info = self.instance.get_public_url_info(link)

            leech_file = LeechFile(
                link=link,
                name=file_info['name'],
                remote_folder=file_info['name'],
                tool=LeechFileTool.MEGA
            )
            
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
            
            leech_files.append(leech_file)

        elif '/folder/' in link:
            pass

        return leech_files


instance = Mega()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
