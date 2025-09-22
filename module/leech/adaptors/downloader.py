import datetime

from celery.result import AsyncResult
from celery.worker.request import Request
from loguru import logger
from celery.apps.worker import Worker
from typing import Callable, TypeAlias

from constants.worker import WorkerStatus, Queue
from celery.utils.dispatch import Signal
from celery.worker.consumer import Consumer

from module.leech.beans.leech_message import LeechMessage
from module.leech.beans.leech_task import LeechTask
from module.leech.constants.message import MessageStatus
from module.leech.constants.task import TaskStatus, TaskType
from module.leech.utils.message import format_result_message
from tool.celery_client import celery_client
from module.leech.beans.leech_file import LeechFile
from module.leech.utils.adaptor import setup_services
from module.leech.constants.leech_file_status import LeechFileStatus
from tool.worker import celeryd_setup_callback, update_worker_status
from celery.signals import worker_shutdown, celeryd_after_setup, worker_ready, task_success, task_received, task_prerun
from tool.mongo_client import EstablishConnection as EstablishMongodbConnection

EstablishMongodbConnection()

DownloadFilter: TypeAlias = Callable[[LeechFile], bool]

EXPORT_NAME_DOWNLOAD_FILTER = 'download_filter'
EXPORT_NAME_DOWNLOAD = 'download'

download_service: dict[DownloadFilter, Callable[[LeechFile], LeechFile]] = \
    setup_services('module/leech/downloaders', EXPORT_NAME_DOWNLOAD_FILTER, EXPORT_NAME_DOWNLOAD)


@celery_client.task()
def process_download(leech_file: LeechFile) -> LeechFile:
    for _filter, func in download_service.items():
        if _filter(leech_file):
            return func(leech_file)

    reason = 'Download service not found.'
    logger.warning(reason)
    leech_file.status = LeechFileStatus.DOWNLOAD_FAIL
    leech_file.reason = reason
    return leech_file


@celeryd_after_setup.connect
def on_download_celeryd_setup(sender: str, instance: Worker, **kwargs):
    celeryd_setup_callback(sender, instance, **kwargs)


@worker_ready.connect
def on_download_worker_ready(signal: Signal, sender: Consumer, **kwargs):
    update_worker_status(sender.hostname, WorkerStatus.READY)


@worker_shutdown.connect
def on_download_worker_shutdown(signal: Signal, sender: Worker, **kwargs):
    update_worker_status(sender.hostname, WorkerStatus.SHUTDOWN)


@task_received.connect
def on_task_received(request: Request, sender, **kwargs):
    LeechTask(
        task_id=request.task_id,
        file_id=request.args[0].id,
        type=TaskType.DOWNLOAD,
        status=TaskStatus.INITIAL
    ).save()


@task_prerun.connect
def on_task_prerun(args, **kwargs):
    leech_file: LeechFile = args[0]
    leech_file.status = LeechFileStatus.DOWNLOADING
    leech_file.updated_at = datetime.datetime.utcnow()
    leech_file.save()


@task_success.connect
def on_task_success(result: LeechFile, sender, **kwargs):
    try:
        result.save()

        LeechTask.objects(task_id=sender.request.id) \
            .update_one(status=TaskStatus.DONE, updated_at=datetime.datetime.utcnow())

        LeechMessage(
            phase=TaskType.DOWNLOAD,
            file_id=result.id,
            content=format_result_message(
                name=result.name,
                size=result.size,
                is_success=result.status == LeechFileStatus.DOWNLOAD_SUCCESS,
                phase=TaskType.DOWNLOAD,
                status=result.status,
                reason=result.reason
            ),
            status=MessageStatus.INITIAL,
            file_status=result.status
        ).save()

    except Exception as e:
        logger.error(e)
