from celery.app.control import Control

from beans.worker import Worker
from constants.worker import Hostname, Project, Queue, WorkerStatus
from module.leech.constants.leech_file_tool import LeechFileTool, LeechFileSyncTool
from tool.celery_client import celery_client
from tool.utils import open_celery_worker_process
from config.config import MAXIMUM_LEECH_WORKER, MAXIMUM_SYNC_WORKER, MAXIMUM_NOTIFY_WORKER

control = Control(app=celery_client)


def generate_queue_names(queue_name: str, tool_class: type) -> str:
    return ','.join([f'{queue_name}@{tool}' for tool in list(
        map(
            lambda x: x[0],
            filter(
                lambda i: not i[0].startswith('_'),
                vars(tool_class).items()
            )
        )
    )])


def start_download_workers():
    open_celery_worker_process(
        Project.LEECH_DOWNLOADER,
        f'{Hostname.FILE_LEECH_WORKER}@{Queue.FILE_DOWNLOAD_QUEUE}',
        generate_queue_names(Queue.FILE_DOWNLOAD_QUEUE, LeechFileTool),
        MAXIMUM_LEECH_WORKER
    )


def start_upload_workers():
    open_celery_worker_process(
        Project.LEECH_UPLOADER,
        f'{Hostname.FILE_SYNC_WORKER}@{Queue.FILE_SYNC_QUEUE}',
        generate_queue_names(Queue.FILE_SYNC_QUEUE, LeechFileSyncTool),
        MAXIMUM_SYNC_WORKER
    )


def start_notify_workers():
    open_celery_worker_process(
        Project.LEECH_NOTIFIER,
        f'{Hostname.FILE_NOTIFY_WORKER}@{Queue.FILE_NOTIFY_QUEUE}',
        Queue.FILE_NOTIFY_QUEUE,
        MAXIMUM_NOTIFY_WORKER
    )


def shutdown_download_workers() -> list[str]:
    workers = Worker.objects(
        hostname__startswith=f'{Hostname.FILE_LEECH_WORKER}@',
        status=WorkerStatus.READY
    ).only('hostname')

    hostnames = [worker.hostname for worker in workers]

    if not hostnames:
        return []

    control.shutdown(destination=hostnames, reply=True)
    return hostnames
