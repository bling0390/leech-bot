import httpx
import re
from urllib.parse import urlparse
from tool.utils import get_redis_unique_key
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


class Pixeldrain(IParser):
    _FILE_ID_PATTERNS = (
        re.compile(r"/(?:u|d)/([^/?#]+)", re.IGNORECASE),
        re.compile(r"/api/file/([^/?#]+)", re.IGNORECASE),
    )
    _LIST_ID_PATTERNS = (
        re.compile(r"/l/([^/?#]+)", re.IGNORECASE),
        re.compile(r"/api/list/([^/?#]+)", re.IGNORECASE),
    )

    def parse_link_filter(self, link: str) -> bool:
        return 'pixeldrain' in link

    def _extract_id(self, path: str, patterns: tuple[re.Pattern, ...]) -> str | None:
        for pattern in patterns:
            match = pattern.search(path)
            if match:
                return match.group(1)
        return None

    def _parse_link_impl(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files = []
        parse_result = urlparse(link)
        path = parse_result.path or ""

        file_id = self._extract_id(path, self._FILE_ID_PATTERNS)
        list_id = self._extract_id(path, self._LIST_ID_PATTERNS)

        if file_id:
            actual_link = f'{parse_result.scheme}://{parse_result.netloc}/api/file/{file_id}'

            response = httpx.get(f'{actual_link}/info').json()

            if not response['success']:
                return []

            leech_file = LeechFile(
                link=actual_link,
                name=response['name'],
                remote_folder=response['name'],
                tool=LeechFileTool.PIXELDRAIN
            )
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
            leech_files.append(leech_file)
        elif list_id:
            response = httpx.get(f'{parse_result.scheme}://{parse_result.netloc}/api/list/{list_id}').json()

            if not response['success']:
                return []

            for file in response['files']:
                leech_file = LeechFile(
                    link=f'{parse_result.scheme}://{parse_result.netloc}/api/file/{file["id"]}',
                    name=file['name'],
                    remote_folder=response['title'],
                    tool=LeechFileTool.PIXELDRAIN
                )
                leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
                leech_files.append(leech_file)
        return leech_files

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        return self._parse_link_impl(link, **kwargs)


instance = Pixeldrain()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
