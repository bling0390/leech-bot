import httpx
from bs4 import BeautifulSoup
from httpx import _status_codes
from urllib.parse import urlparse
from mediafire import MediaFireApi

from tool.utils import get_redis_unique_key
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


class Mediafire(IParser):
    def __int__(self):
        self.instance = MediaFireApi()

    def parse_link_filter(self, link: str) -> bool:
        return 'mediafire' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files: [LeechFile] = []

        parse_result = urlparse(link)

        if '/folder/' in parse_result.path:
            pass

        elif '/file/' in parse_result.path:
            response = httpx.get(link)

            if response.status_code == _status_codes.codes.OK:
                soup = BeautifulSoup(response.text, 'html.parser')

                href = soup.select_one('a#downloadButton').get('href')
                name = href.split('/')[-1]

                leech_file = LeechFile(
                    link=href,
                    name=name,
                    remote_folder=name,
                    tool=LeechFileTool.MEDIAFIRE
                )

                leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'

                leech_files.append(leech_file)

        return leech_files


instance = Mediafire()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
