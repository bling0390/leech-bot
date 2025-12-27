import httpx
from urllib.parse import urlparse
from tool.utils import get_redis_unique_key
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


class Pixeldrain(IParser):
    def parse_link_filter(self, link: str) -> bool:
        return 'pixeldrain' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files = []
        parse_result = urlparse(link)

        path_parts = [part for part in (parse_result.path or '').split('/') if part]
        if not path_parts:
            return []

        mode = path_parts[0]

        file_id: str | None = None
        list_id: str | None = None

        if mode in ('u', 'd'):
            file_id = path_parts[1] if len(path_parts) > 1 else None
        elif mode == 'l':
            list_id = path_parts[1] if len(path_parts) > 1 else None
        elif mode == 'api' and len(path_parts) >= 3:
            api_type = path_parts[1]
            if api_type == 'file':
                file_id = path_parts[2]
            elif api_type == 'list':
                list_id = path_parts[2]

        if file_id is not None:
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
        elif list_id is not None:
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


instance = Pixeldrain()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
