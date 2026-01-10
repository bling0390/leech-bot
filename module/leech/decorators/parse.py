import functools
from celery import chain
from loguru import logger
from constants.worker import Queue
from tool.utils import get_redis_unique_key
from tool.celery_client import celery_client
from module.leech.beans.leech_file import LeechFile
from config.config import CELERY_DOWNLOAD_TASK_FUNCTION_NAME, CELERY_UPLOAD_TASK_FUNCTION_NAME


def catch_parse_exception(f):
    @functools.wraps(f)
    def wrapper(self, link: str, **kwargs) -> list[LeechFile]:

        try:
            return f(self, link, **kwargs)
        except Exception as e:
            logger.error(f'Error parse link {link}: {str(e)}')

        return []

    return wrapper


def create_document(f):
    @functools.wraps(f)
    def wrapper(self, link: str, **kwargs) -> list[LeechFile]:
        leech_files: list[LeechFile] = f(self, link, **kwargs)

        queued_files = []

        for leech_file in leech_files:
            try:
                leech_file.sync_tool = kwargs.get('sync_tool')
                leech_file.sync_path = kwargs.get('sync_path')
                leech_file.file_hash = get_redis_unique_key(leech_file)

                chain(
                    celery_client.signature(
                        CELERY_DOWNLOAD_TASK_FUNCTION_NAME,
                        (leech_file,),
                        queue=f'{Queue.FILE_DOWNLOAD_QUEUE}@{leech_file.tool}'
                    ),
                    celery_client.signature(
                        CELERY_UPLOAD_TASK_FUNCTION_NAME,
                        queue=f'{Queue.FILE_SYNC_QUEUE}@{leech_file.sync_tool}'
                    )
                ).apply_async()

                leech_file.save(force_insert=True)
                queued_files.append(leech_file)
            except Exception as e:
                logger.error(e)
                pass

        return queued_files

    return wrapper
