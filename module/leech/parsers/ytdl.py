import yt_dlp

from tool.utils import get_redis_unique_key
from yt_dlp.extractor import list_extractors
from config.config import BOT_DOWNLOAD_LOCATION
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.parse import catch_parse_exception, create_document


class YTDL(IParser):
    def parse_link_filter(self, link: str) -> bool:
        return next(
            (ie.ie_key() for ie in list_extractors() if ie.suitable(link) and ie.ie_key() != 'Generic'),
            None
        ) is not None

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files = []

        with yt_dlp.YoutubeDL() as ydl:
            file_info = ydl.extract_info(link, download=False)

            if '_type' in file_info and file_info['_type'] == 'playlist':
                for entry in file_info['entries']:
                    leech_file = LeechFile(
                        link=entry['webpage_url'],
                        name=f'{file_info["title"]}.{file_info["ext"]}',
                        remote_folder=file_info['id'],
                        tool=LeechFileTool.YT_DLP
                    )

                    leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'

                    leech_files.append(leech_file)

            else:
                leech_file = LeechFile(
                    link=link,
                    remote_folder=file_info['id'],
                    name=f'{file_info["title"]}.{file_info["ext"]}',
                    tool=LeechFileTool.YT_DLP
                )

                leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'

                leech_files.append(leech_file)

        return leech_files


instance = YTDL()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
