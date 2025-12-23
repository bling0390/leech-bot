import asyncio
import datetime
import signal

from celery.app.control import Control
from celery.result import AsyncResult
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.config import LEECH_TERMINATE_CONTROL_TIMEOUT, LEECH_TERMINATE_SIGNAL
from constants.worker import Project
from module.leech.beans.leech_file import LeechFile
from module.leech.beans.leech_task import LeechTask
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.constants.task import TaskStatus, TaskType
from module.leech.utils.button import get_bottom_buttons
from module.leech.utils.message import send_message_to_admin
from tool.celery_client import celery_client
from tool.utils import is_authorized_user

COMMAND_PREFIX = 'leech_terminate_'
control_instance = Control(app=celery_client)


class Scope:
    PENDING = 'pending'
    ACTIVE = 'active'
    ALL = 'all'


def _parse_signal(sig: str) -> int:
    return getattr(signal, sig, signal.SIGTERM)


def _get_active_task_ids(task_type: TaskType) -> set[str]:
    inspect = control_instance.inspect()
    active = inspect.active() or {}
    reserved = inspect.reserved() or {}
    task_name = f'{Project.LEECH_DOWNLOADER}.process_download' if task_type == TaskType.DOWNLOAD else \
        f'{Project.LEECH_UPLOADER}.process_upload'

    ids: set[str] = set()
    for tasks in list(active.values()) + list(reserved.values()):
        for task in tasks or []:
            if task.get('name') == task_name:
                ids.add(task.get('id'))
    return ids


async def _revoke_tasks(task_ids: set[str], should_terminate: bool) -> int:
    if not task_ids:
        return 0

    signal_to_use = _parse_signal(LEECH_TERMINATE_SIGNAL) if should_terminate else None
    count = 0
    for task_id in task_ids:
        try:
            await asyncio.to_thread(
                AsyncResult(task_id, app=celery_client).revoke,
                terminate=should_terminate,
                signal=signal_to_use
            )
            count += 1
        except Exception:
            continue
    return count


def _build_scope_buttons(task_type: str, pending_count: int, active_count: int) -> InlineKeyboardMarkup:
    parts = []
    parts.append([
        InlineKeyboardButton(
            text=f'Pending only ({pending_count})',
            callback_data=f'{COMMAND_PREFIX}do_{task_type}_{Scope.PENDING}',
        )
    ])
    parts.append([
        InlineKeyboardButton(
            text=f'Running only ({active_count})',
            callback_data=f'{COMMAND_PREFIX}do_{task_type}_{Scope.ACTIVE}',
        )
    ])
    parts.append([
        InlineKeyboardButton(
            text=f'All ({pending_count + active_count})',
            callback_data=f'{COMMAND_PREFIX}do_{task_type}_{Scope.ALL}',
        )
    ])
    parts.append(get_bottom_buttons('', should_have_return=False))
    return InlineKeyboardMarkup(parts)


@Client.on_callback_query(filters.regex(f'^{COMMAND_PREFIX}'))
async def interact_callback(_, query):
    payload = query.data.removeprefix(COMMAND_PREFIX)
    await query.message.delete()

    if payload.startswith('type_'):
        task_type_str = payload.removeprefix('type_')
        pending_download = LeechTask.objects(status=TaskStatus.INITIAL, type__=TaskType.DOWNLOAD).count()
        pending_upload = LeechTask.objects(status=TaskStatus.INITIAL, type__=TaskType.UPLOAD).count()
        active_download = len(_get_active_task_ids(TaskType.DOWNLOAD))
        active_upload = len(_get_active_task_ids(TaskType.UPLOAD))

        if task_type_str == 'BOTH':
            pending_count = pending_download + pending_upload
            active_count = active_download + active_upload
        elif task_type_str == TaskType.DOWNLOAD.value:
            pending_count = pending_download
            active_count = active_download
        else:
            pending_count = pending_upload
            active_count = active_upload

        await send_message_to_admin(
            '\n'.join([
                '<b>Select scope to terminate.</b>',
                f'Pending: {pending_count}, Running: {active_count}'
            ]),
            should_auto_delete=False,
            chat_id=query.message.chat.id,
            reply_markup=_build_scope_buttons(task_type_str, pending_count, active_count)
        )
        return

    if payload.startswith('do_'):
        _, type_str, scope = payload.split('_', 2)
        task_types = [TaskType.DOWNLOAD, TaskType.UPLOAD] if type_str == 'BOTH' else [TaskType(type_str)]

        pending_ids: set[str] = set()
        active_ids: set[str] = set()
        for t in task_types:
            if scope in (Scope.PENDING, Scope.ALL):
                pending_ids.update({task.task_id for task in LeechTask.objects(status=TaskStatus.INITIAL, type__=t).only('task_id')})
            if scope in (Scope.ACTIVE, Scope.ALL):
                active_ids.update(_get_active_task_ids(t))

        revoke_pending = await _revoke_tasks(pending_ids, should_terminate=False)
        revoke_running = await _revoke_tasks(active_ids, should_terminate=True)

        affected_task_ids = pending_ids.union(active_ids)
        now = datetime.datetime.utcnow()
        if affected_task_ids:
            tasks = list(LeechTask.objects(task_id__in=list(affected_task_ids)).only('task_id', 'file_id', 'type'))
            LeechTask.objects(task_id__in=list(affected_task_ids)).update(
                set__status=TaskStatus.TERMINATED,
                set__updated_at=now
            )
            download_file_ids = [t.file_id for t in tasks if t.type == TaskType.DOWNLOAD]
            upload_file_ids = [t.file_id for t in tasks if t.type == TaskType.UPLOAD]
            if download_file_ids:
                LeechFile.objects(id__in=download_file_ids).update(
                    set__status=LeechFileStatus.TERMINATED,
                    set__reason='Terminated by user',
                    set__updated_at=now
                )
            if upload_file_ids:
                LeechFile.objects(id__in=upload_file_ids).update(
                    set__upload_status=LeechFileStatus.TERMINATED,
                    set__upload_reason='Terminated by user',
                    set__updated_at=now
                )

        await send_message_to_admin(
            '\n'.join([
                '<b>Terminate result</b>',
                f'Pending revoked: {revoke_pending}/{len(pending_ids)}',
                f'Running terminated: {revoke_running}/{len(active_ids)}',
                f'Total affected tasks: {len(affected_task_ids)}'
            ]),
            should_auto_delete=False,
            chat_id=query.message.chat.id
        )
        return


@Client.on_message(filters.command('leech terminate') & (filters.private | filters.group | filters.channel) & is_authorized_user)
async def leech_terminate(_: Client, message: Message):
    await message.reply(
        text='\n\n'.join([
            '<b>Choose task type you wanna terminate.</b>'
        ]),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text='Only download tasks',
                    callback_data=f'{COMMAND_PREFIX}type_{TaskType.DOWNLOAD.value}',
                )
            ],
            [
                InlineKeyboardButton(
                    text='Only upload tasks',
                    callback_data=f'{COMMAND_PREFIX}type_{TaskType.UPLOAD.value}',
                )
            ],
            [
                InlineKeyboardButton(
                    text='Both',
                    callback_data=f'{COMMAND_PREFIX}type_BOTH',
                )
            ],
            get_bottom_buttons('', should_have_return=False)
        ])
    )
