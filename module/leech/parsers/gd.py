import re
from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_bunkr_file import LeechBunkrFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document

ID_PATTERNS = [
    re.compile("/file/d/([0-9A-Za-z_-]{10,})(?:/|$)", re.IGNORECASE),
    re.compile("/folders/([0-9A-Za-z_-]{10,})(?:/|$)", re.IGNORECASE),
    re.compile("id=([0-9A-Za-z_-]{10,})(?:&|$)", re.IGNORECASE),
    re.compile("([0-9A-Za-z_-]{10,})", re.IGNORECASE),
]


def get_id_from_url(url: str):
    for pattern in ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)


class GD(IParser):

    def parse_link_filter(self, link: str) -> bool:
        return 'drive.google.com' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files: list[LeechFile] = []

        if '/file/' in link or '/uc?' in link:
            file_id = get_id_from_url(link)

            if file_id is not None:
                leech_files.append(LeechBunkrFile(
                    link=link,
                    actual_link=f'https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0',
                    tool=LeechFileTool.GD
                ))

        return leech_files


instance = GD()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
