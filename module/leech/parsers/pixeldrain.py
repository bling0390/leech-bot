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

        file_id = parse_result.path.split('/')[-1] if parse_result.path is not None else None

        if file_id is None:
            return []

        if '/u/' in parse_result.path:
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
        elif '/l/' in parse_result.path:
            response = httpx.get(f'{parse_result.scheme}://{parse_result.netloc}/api/list/{file_id}').json()

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
