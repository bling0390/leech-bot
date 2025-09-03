import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tool.utils import get_request_header
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.beans.leech_bunkr_file import LeechBunkrFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


class CyberDrop(IParser):

    def parse_link_filter(self, link: str) -> bool:
        return 'cyberdrop' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files = []
        parse_result = urlparse(link)

        response = httpx.get(link, headers=get_request_header(link))

        soup = BeautifulSoup(response.text, 'html.parser')

        if '/f/' in parse_result.path:
            leech_files.append(
                LeechBunkrFile(
                    link=link,
                    tool=LeechFileTool.CYBERDROP
                )
            )
        elif '/a/' in parse_result.path:
            for link in soup.find_all('div', {'class': 'image-container'}):
                leech_files.append(LeechBunkrFile(
                    link=f'{parse_result.scheme}://{parse_result.netloc}{link.find("a", {"class": "image"})["href"]}',
                    remote_folder=soup.find('h1', {'id': 'title'})['title'],
                    tool=LeechFileTool.CYBERDROP
                ))

        return leech_files


instance = CyberDrop()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
