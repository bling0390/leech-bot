import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from tool.utils import get_redis_unique_key, get_request_header
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


class Saint(IParser):
    def parse_link_filter(self, link: str) -> bool:
        return 'saint' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files: [LeechFile] = []
        parse_result = urlparse(link)

        response = httpx.get(link, headers=get_request_header(link))

        soup = BeautifulSoup(response.text, 'html.parser')

        if '/embed/' in parse_result.path:
            video = soup.select_one('video[id=main-video] source')

            # video not found
            if video is None:
                return []

            src = video.get('src')

            leech_file = LeechFile(
                link=src,
                name=src.split('/')[-1],
                remote_folder=parse_result.path.split('/')[-1],
                tool=LeechFileTool.SAINT
            )
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
            leech_files.append(leech_file)
        elif '/d/' in parse_result.path:
            src = soup.select_one('a').get('href')
            leech_file = LeechFile(
                link=src,
                name=httpx
                .get(src, headers=get_request_header(link))
                .headers['content-disposition']
                .split('filename=')[-1]
                .strip('"'),
                remote_folder=parse_result.path.split('/')[-1],
                tool=LeechFileTool.SAINT
            )
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
            leech_files.append(leech_file)

        return leech_files


instance = Saint()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
