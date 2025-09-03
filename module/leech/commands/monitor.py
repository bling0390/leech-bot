import datetime

import prettytable as pt

from beans.worker import Worker
from tool.utils import is_admin
from pyrogram.types import Message
from pyrogram import Client, filters
from constants.worker import WorkerStatus, Hostname
from module.leech.beans.leech_file import LeechFile
from module.leech.beans.leech_task import LeechTask
from config.config import FAILED_TASK_EXPIRE_AFTER_DAYS
from module.leech.utils.message import send_message_to_admin
from module.leech.constants.task import TaskStatus, TaskType
from module.leech.constants.leech_file_status import LeechFileStatus


def get_task_count(task_status: TaskStatus, task_type: TaskType) -> int:
    return LeechTask.objects(
        status=task_status,
        type__=task_type,
        created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)
    ).count()


@Client.on_message(filters.command('leech monitor') & filters.private & is_admin)
async def leech_monitor(_: Client, message: Message):
    m: Message = await send_message_to_admin('Got it, please wait...', False)
    title = f'Statistic within {FAILED_TASK_EXPIRE_AFTER_DAYS} days'
    table = pt.PrettyTable(['Item', 'Current'])
    table.border = True
    table.preserve_internal_border = False
    table.header = False
    table._max_width = {'Item': 35, 'Current': 10}
    table.valign['Item'] = 'm'
    table.valign['Current'] = 'm'

    table.add_row(['Tasks in download queue', get_task_count(TaskStatus.INITIAL, TaskType.DOWNLOAD)], divider=True)
    table.add_row(['Tasks in upload queue', get_task_count(TaskStatus.INITIAL, TaskType.UPLOAD)], divider=True)

    table.add_row(
        [
            'Number of failed task',
            LeechFile.objects(
                status=LeechFileStatus.DOWNLOAD_FAIL,
                upload_status=LeechFileStatus.UPLOAD_FAIL,
                created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)
            ).count()
        ],
        divider=True
    )

    table.add_row(
        [
            'Number of successful task',
            LeechFile.objects(
                status=LeechFileStatus.DOWNLOAD_SUCCESS,
                upload_status=LeechFileStatus.UPLOAD_SUCCESS,
                created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)
            ).count()
        ],
        divider=True
    )

    number_of_download_worker = 0
    number_of_upload_worker = 0
    download_queue_concurrency = {}
    upload_queue_concurrency = {}
    for worker in Worker.objects(status=WorkerStatus.READY):
        if Hostname.FILE_LEECH_WORKER in worker.hostname:
            number_of_download_worker += 1

            for queue in worker.queue.split(','):
                if queue not in download_queue_concurrency:
                    download_queue_concurrency[queue] = 0
                download_queue_concurrency[queue] += worker.concurrency
        elif Hostname.FILE_SYNC_WORKER in worker.hostname:
            number_of_upload_worker += 1

            for queue in worker.queue.split(','):
                if queue not in upload_queue_concurrency:
                    upload_queue_concurrency[queue] = 0
                upload_queue_concurrency[queue] += worker.concurrency

    table.add_row(['Number of download worker', number_of_download_worker], divider=True)
    table.add_row(['Number of upload worker', number_of_upload_worker], divider=True)

    for queue, concurrency in download_queue_concurrency.items():
        table.add_row(
            [
                f'Concurrency of {queue.split("@")[1].lower()}',
                concurrency
            ],
            divider=True
        )

    for queue, concurrency in upload_queue_concurrency.items():
        table.add_row(
            [
                f'Concurrency of {queue.split("@")[1].lower()}',
                concurrency
            ],
            divider=True
        )

    await m.delete()
    await send_message_to_admin(f'<pre>| \n| {title}\n| \n{table.get_string()}</pre>', False)
