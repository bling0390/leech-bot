import httpx
import datetime
from os import path
from urllib import parse
from loguru import logger
from httpx import _status_codes

from module.leech.interfaces.uploader import IUploader
from tool.user_agents import get_random_user_agent
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.constants.leech_file_tool import LeechFileSyncTool
from config.config import SHOULD_USE_DATETIME_CATEGORY, ALIST_HOST, ALIST_TOKEN
from module.leech.decorators.upload import catch_upload_exception, clean_temp_file, check_before_upload


class Alist(IUploader):
    def upload_filter(self, sync_tool: str):
        return sync_tool == LeechFileSyncTool.ALIST

    @catch_upload_exception
    @check_before_upload
    @clean_temp_file
    def upload(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        logger.info(f'Uploading file "{leech_file.name}" to "{leech_file.sync_path}".')

        full_name = leech_file.get_full_name()

        response = httpx.put(
            url=f'{ALIST_HOST}/api/fs/put',
            headers={
                'UserAgent': get_random_user_agent(),
                'As-Task': getattr(kwargs, 'as_task', 'true'),
                'Authorization': ALIST_TOKEN,
                'File-Path': parse.quote('/'.join(list(filter(lambda x: x is not None, [
                    leech_file.sync_path,
                    str(datetime.date.today()) if SHOULD_USE_DATETIME_CATEGORY else None,
                    getattr(leech_file, 'remote_folder'),
                    leech_file.name
                ])))),
                'Content-Length': f'{path.getsize(full_name)}',
            },
            content=open(full_name, 'rb').read(),
            timeout=None
        ).json()

        leech_file.upload_status = LeechFileStatus.UPLOAD_SUCCESS if \
            response['code'] == _status_codes.codes.OK else \
            LeechFileStatus.DOWNLOAD_FAIL
        leech_file.upload_reason = None if response['code'] == _status_codes.codes.OK else response['message']

        logger.info(f'File upload {leech_file.status}, reason: {leech_file.upload_reason}, response: {response}')

        # refresh list when success
        if response['code'] == _status_codes.codes.OK:
            try:
                httpx.post(
                    url=f'{ALIST_HOST}/api/fs/list',
                    headers={
                        'Authorization': ALIST_TOKEN,
                    },
                    data={
                        'path': leech_file.sync_path,
                        'password': '',
                        'page': 1,
                        'per_page': 0,
                        'refresh': True
                    },
                    timeout=None
                )
            except httpx.RequestError:
                logger.error(f'Failed to refresh list for storage "{leech_file.sync_path}".')
                pass

        return leech_file


instance = Alist()
upload_filter = instance.upload_filter
upload = instance.upload
