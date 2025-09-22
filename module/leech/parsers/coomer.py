import httpx
from bs4 import BeautifulSoup
from httpx import _status_codes
from urllib.parse import urlparse, quote
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.parser import IParser
from tool.utils import get_redis_unique_key, get_request_header
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


class Coomer(IParser):
    def parse_link_filter(self, link: str) -> bool:
        return 'coomer' in link or 'kemono' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        parse_result = urlparse(link)

        if '/post/' in parse_result.path:
            response = httpx.get(link, headers=get_request_header(link))

            if response.status_code != _status_codes.codes.OK:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            author = soup.find('a', class_='post__user-name')

            if author:
                remote_folder = author.text.strip()
            else:
                remote_folder = soup.find('meta', property='og:image')['content'].split('/')[-1].split('-')[0]

            leech_files = []

            for element in soup.find_all('a', class_=['post__attachment-link', 'fileThumb']):
                leech_file = LeechFile(
                    link=element['href'],
                    name=quote(element['download']),
                    remote_folder=remote_folder,
                    tool=LeechFileTool.COOMER
                )
                leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
                leech_files.append(leech_file)

            return leech_files

        elif '/user/' in parse_result.path:
            page = 1
            leech_files = []

            while True:
                if page > 1:
                    return leech_files

                response = httpx.get(
                    f'{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?o={(page - 1) * 50}'
                )

                if response.status_code != _status_codes.codes.OK:
                    return leech_files

                soup = BeautifulSoup(response.text, 'html.parser')

                for element in soup.css.select('.post-card--preview > a'):
                    leech_files.extend(
                        self.parse_link(f'{parse_result.scheme}://{parse_result.netloc}{element["href"]}')
                    )

                page += 1

        return []


instance = Coomer()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link

