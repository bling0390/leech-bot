import os
import httpx
import shutil
import datetime
import functools
from httpx import _status_codes
from urllib.parse import urlparse

from tool.user_agents import get_random_user_agent
from module.leech.beans.leech_file import LeechFile
from tool.utils import get_redis_unique_key, clean_local_file
from module.leech.constants.leech_file_status import LeechFileStatus
from config.config import SKIP_DUPLICATE_LINK_WITHIN_DAYS, WRITE_STREAM_CONNECT_TIMEOUT


def check_before_download(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        # check if file has been download more than once
        record = LeechFile.objects(
            file_hash=get_redis_unique_key(leech_file),
            status=LeechFileStatus.DOWNLOAD_SUCCESS,
            upload_status=LeechFileStatus.UPLOAD_SUCCESS,
            created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=SKIP_DUPLICATE_LINK_WITHIN_DAYS)
        ).order_by('-created_at').first()

        if record is not None:
            leech_file.status = LeechFileStatus.SKIP_DOWNLOAD
            leech_file.reason = f'File has been downloaded within {SKIP_DUPLICATE_LINK_WITHIN_DAYS} days'
            return leech_file

        full_name = leech_file.get_full_name()

        # check if file already exist
        if os.path.exists(full_name):
            file_size = os.path.getsize(full_name)

            if file_size > 0:
                leech_file.status = LeechFileStatus.DOWNLOAD_SUCCESS
                leech_file.size = file_size
                leech_file.reason = 'File already exist.'
                return leech_file

        os.makedirs(leech_file.location, exist_ok=True)

        return f(self, leech_file, **kwargs)

    return wrapper


def check_after_download(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        temp_full_name = leech_file.get_temp_full_name()

        if os.path.exists(temp_full_name) and leech_file.size != os.path.getsize(temp_full_name):
            leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
            leech_file.reason = f'{temp_full_name} size check failed, file could be broken.'
            return leech_file

        return f(self, leech_file, **kwargs)

    return wrapper


def write_file(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        if leech_file.status != LeechFileStatus.DOWNLOADING:
            return leech_file

        parse_result = urlparse(leech_file.link)

        with httpx.stream('get', getattr(leech_file, 'actual_link', leech_file.link), headers={
            'User-Agent': get_random_user_agent(),
            'Referer': f'{parse_result.scheme}://{parse_result.netloc}'
        }, timeout=WRITE_STREAM_CONNECT_TIMEOUT) as r:
            if r.status_code != _status_codes.codes.OK:
                leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
                leech_file.reason = f"Error downloading \"{leech_file.name}\": {r.status_code}."
                return leech_file

            leech_file.size = int(r.headers.get('content-length', -1))

            with open(leech_file.get_temp_full_name(), 'wb') as file:
                for chunk in r.iter_bytes(chunk_size=8192):
                    if chunk is not None:
                        file.write(chunk)

        return f(self, leech_file, **kwargs)

    return wrapper


def move_file(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        temp_full_name = leech_file.get_temp_full_name()
        if os.path.exists(temp_full_name) and os.path.getsize(temp_full_name) == leech_file.size:
            shutil.move(temp_full_name, leech_file.get_full_name())
            leech_file.status = LeechFileStatus.DOWNLOAD_SUCCESS
            return leech_file

        return f(self, leech_file, **kwargs)

    return wrapper


def catch_download_exception(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        try:
            f(self, leech_file, **kwargs)
        except Exception as e:
            leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
            leech_file.reason = str(e)
            clean_local_file(leech_file)

            return leech_file

        return leech_file

    return wrapper
