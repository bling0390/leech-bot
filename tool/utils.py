import os
import hashlib
import subprocess
import urllib.parse
from typing import Union
from shutil import rmtree

from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

from config.config import TELEGRAM_ADMIN_ID, ALIST_WEB, ALIST_TOKEN, ALIST_HOST
from module.leech.beans.leech_file import LeechFile
from constants.worker import Project
from tool.user_agents import get_random_user_agent


async def __is_admin(_, __, update: Union[Message, CallbackQuery]) -> bool:
    return update.from_user.id == TELEGRAM_ADMIN_ID


is_admin = filters.create(__is_admin)


def get_redis_unique_key(leech_file: LeechFile) -> str:
    return hashlib.md5(urllib.parse.quote(
        f'{leech_file.tool}_{getattr(leech_file, "remote_folder", "")}_{leech_file.name}'
    ).encode()).hexdigest()


def get_request_header(link: str):
    parse_result = urllib.parse.urlparse(link)

    return {
        'User-Agent': get_random_user_agent(),
        'Referer': f'{parse_result.scheme}://{parse_result.netloc}'
    }


def is_alist_available():
    return all([ALIST_WEB, ALIST_TOKEN]) or all([ALIST_HOST, ALIST_TOKEN])


def open_celery_worker_process(project: Project, hostname: str, queues: str, concurrency: int):
    subprocess.Popen([
        'celery',
        '-A',
        project,
        'worker',
        '--loglevel=INFO',
        '--without-gossip',
        '--pool=solo',
        f'--hostname={hostname}',
        f'--queues={queues}',
        f'--concurrency={concurrency}'
    ])


def convert_bytes(byte_amount: int) -> str:
    if byte_amount > 1024 ** 5:
        return f"{byte_amount / (1024 ** 5):.2f} PiB"
    elif byte_amount > 1024 ** 4:
        return f"{byte_amount / (1024 ** 4):.2f} TiB"
    elif byte_amount > 1024 ** 3:
        return f"{byte_amount / (1024 ** 3):.2f} GiB"
    elif byte_amount > 1024 ** 2:
        return f"{byte_amount / (1024 ** 2):.2f} MiB"
    elif byte_amount > 1024:
        return f"{byte_amount / 1024:.2f} KiB"
    else:
        return f"{byte_amount:.2f} B"


def clean_local_file(leech_file: LeechFile):
    full_name = leech_file.get_full_name()

    if os.path.isfile(full_name) or os.path.islink(full_name):
        os.remove(full_name)

    if leech_file.location is not None and os.path.exists(leech_file.location) and len(
            os.listdir(leech_file.location)) == 0:
        rmtree(leech_file.location)
