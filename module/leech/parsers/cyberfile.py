import re
import httpx
from typing import Literal
from bs4 import BeautifulSoup
from httpx._models import Cookies
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.beans.leech_bunkr_file import LeechBunkrFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


def iterate_folders(
    link: str,
    node_id: int | str,
    page_type: Literal['nonaccountshared'] | Literal['folder'],
    cookies: Cookies = None
) -> list[LeechFile]:
    leech_files: list[LeechFile] = []
    page = 1

    while True:
        soup = BeautifulSoup(httpx.post(f'https://cyberfile.me/account/ajax/load_files', data={
            'pageType': page_type,
            'nodeId': node_id,
            'pageStart': page,
            'perPage': 0,
            'filterOrderBy': ''
        }, headers={
            'Referer': link
        }, cookies=cookies).json()['html'], 'html.parser')

        for item in soup.select('div[class=fileListing] div[class*=fileItem]'):
            if item.get('folderId') is not None:
                leech_files.extend(iterate_folders(link, int(item.get('folderId')), page_type))
            elif item.get('folderid') is not None:
                leech_files.extend(iterate_folders(link, int(item.get('folderid')), page_type, cookies))
            else:
                leech_files.append(LeechBunkrFile(
                    link=item.get('dtfullurl'),
                    tool=LeechFileTool.CYBERFILE
                ))

        page += 1

        if page > int(soup.select_one('input#rspTotalPages').get('value', '0')):
            break

    return leech_files


class Cyberfile(IParser):
    def parse_link_filter(self, link: str) -> bool:
        return 'cyberfile' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files: list[LeechFile] = []

        if '/folder/' in link:
            leech_files.extend(
                iterate_folders(
                    link,
                    int(re.findall(r"loadImages\('folder', '(\d+)',", httpx.get(link).text)[0]),
                    'folder'
                )
            )
        elif '/shared/' in link:
            leech_files.extend(
                iterate_folders(
                    link,
                    '',
                    'nonaccountshared',
                    httpx.get(link).cookies
                )
            )
        else:
            leech_files.append(LeechBunkrFile(
                link=link,
                tool=LeechFileTool.CYBERFILE
            ))

        return list(filter(lambda x: x is not None, leech_files))


instance = Cyberfile()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
