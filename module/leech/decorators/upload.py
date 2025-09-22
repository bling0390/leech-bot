import functools
from loguru import logger

from tool.utils import clean_local_file
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_status import LeechFileStatus


def catch_upload_exception(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        try:
            return f(self, leech_file, **kwargs)
        except Exception as e:
            logger.error(f'Failed to upload file "{leech_file.name}" to "{leech_file.sync_path}".', str(e))
            leech_file.upload_status = LeechFileStatus.UPLOAD_FAIL
            leech_file.upload_reason = str(e)

        return leech_file

    return wrapper


def check_before_upload(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        if leech_file.status == LeechFileStatus.SKIP_DOWNLOAD and \
                leech_file.upload_status == LeechFileStatus.UPLOADING:
            leech_file.upload_status = LeechFileStatus.SKIP_UPLOAD
            return leech_file

        if leech_file.status != LeechFileStatus.DOWNLOAD_SUCCESS or \
                leech_file.upload_status != LeechFileStatus.UPLOADING:
            leech_file.upload_reason = \
                f'File may not download properly or upload process has been interrupted.'
            leech_file.upload_status = LeechFileStatus.SKIP_UPLOAD
            return leech_file

        return f(self, leech_file, **kwargs)

    return wrapper


def clean_temp_file(f):
    @functools.wraps(f)
    def wrapper(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        leech_file: LeechFile = f(self, leech_file, **kwargs)

        if leech_file.upload_status == LeechFileStatus.UPLOAD_SUCCESS:
            clean_local_file(leech_file)

        return leech_file

    return wrapper
