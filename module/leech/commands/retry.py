import datetime
from celery import chain
from tool.utils import is_authorized_user
from constants.worker import Queue
from pyrogram import Client, filters
from module.leech.beans.leech_file import LeechFile
from config.config import FAILED_TASK_EXPIRE_AFTER_DAYS, LEECH_RETRY_BATCH_SIZE
from module.leech.utils.button import get_bottom_buttons
from module.leech.adaptors.uploader import process_upload
from module.leech.utils.message import send_message_to_admin
from module.leech.adaptors.downloader import process_download
from module.leech.constants.leech_file_status import LeechFileStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

COMMAND_PREFIX = 'leech_retry_'
COMMAND_PREFIX_SINGLE = f'{COMMAND_PREFIX}single_'
BATCH_SIZE = max(1, LEECH_RETRY_BATCH_SIZE)


def retry_specific_tasks(
    filter_status: LeechFileStatus,
    offset: int = 0,
    limit: int = BATCH_SIZE
) -> tuple[int, int]:
    """
    Returns (processed_count, total_count)
    """
    base_query = LeechFile.objects(
        status=filter_status,
        created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)
    ) if filter_status == LeechFileStatus.DOWNLOAD_FAIL else LeechFile.objects(
        upload_status=filter_status,
        created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)
    )

    total_count = base_query.count()
    leech_files: list[LeechFile] = list(
        base_query.order_by('-created_at').skip(offset).limit(limit)
    )

    if len(leech_files) == 0:
        return 0, total_count

    now = datetime.datetime.utcnow()
    file_ids = [leech_file.id for leech_file in leech_files]

    LeechFile.objects(id__in=file_ids).update(
        set__status=LeechFileStatus.INITIAL,
        set__upload_status=LeechFileStatus.INITIAL,
        set__updated_at=now
    )

    for leech_file in leech_files:
        leech_file.status = LeechFileStatus.INITIAL
        leech_file.upload_status = LeechFileStatus.INITIAL
        leech_file.updated_at = now
        create_pending_task(leech_file)

    return len(leech_files), total_count


@Client.on_callback_query(filters.regex(f'^{COMMAND_PREFIX_SINGLE}'))
async def retry_single_task(_, query):
    await query.message.delete()

    leech_file: LeechFile | None = LeechFile.objects(id=query.data.removeprefix(COMMAND_PREFIX_SINGLE)).first()

    if leech_file is not None and \
            leech_file.created_at > (
                datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)):
        leech_file.status = LeechFileStatus.INITIAL
        leech_file.upload_status = LeechFileStatus.INITIAL
        leech_file.updated_at = datetime.datetime.utcnow()
        leech_file.save()

        create_pending_task(leech_file)

        await send_message_to_admin('✅ <b>Task has retried!</b>', chat_id=query.message.chat.id)
    else:
        await send_message_to_admin('❌ <b>Task not exist or expired</b>', chat_id=query.message.chat.id)


@Client.on_callback_query(filters.regex(f'^{COMMAND_PREFIX}'))
async def interact_callback(_, query):
    status, offset = _parse_status_and_offset(query.data.removeprefix(COMMAND_PREFIX))
    next_offset = offset + BATCH_SIZE

    await query.message.delete()

    if status == 'both':
        download_count, download_total = retry_specific_tasks(LeechFileStatus.DOWNLOAD_FAIL, offset=offset)
        upload_count, upload_total = retry_specific_tasks(LeechFileStatus.UPLOAD_FAIL, offset=offset)
        remaining = max(download_total - next_offset, 0) + max(upload_total - next_offset, 0)
        message = '\n'.join([
            f'✅ <b>{download_count + upload_count} tasks has retried in this batch!</b>',
            f'📥 Download retried: {download_count}/{download_total}',
            f'📤 Upload retried: {upload_count}/{upload_total}',
            f'⏳ Remaining (approx): {remaining}'
        ])
    else:
        count, total = retry_specific_tasks(LeechFileStatus(status), offset=offset)
        remaining = max(total - next_offset, 0)
        message = '\n'.join([
            f'✅ <b>{count} tasks has retried in this batch!</b>',
            f'📦 Total failed tasks: {total}',
            f'⏳ Remaining (approx): {remaining}'
        ])

    reply_markup = _build_continue_markup(status, next_offset, remaining)

    await send_message_to_admin(message, chat_id=query.message.chat.id, reply_markup=reply_markup)


def create_pending_task(leech_file: LeechFile):
    chain(
        process_download.signature(
            (leech_file,),
            queue=f'{Queue.FILE_DOWNLOAD_QUEUE}@{leech_file.tool}'
        ),
        process_upload.signature(queue=f'{Queue.FILE_SYNC_QUEUE}@{leech_file.sync_tool}')
    ).apply_async()


@Client.on_message(filters.command('leech retry') & (filters.private | filters.group | filters.channel) & is_authorized_user)
async def leech_retry(_: Client, message: Message):
    await message.reply(
        text='\n\n'.join([
            f'<b>Tasks will download/upload again if they are failed within {FAILED_TASK_EXPIRE_AFTER_DAYS} days,</b>',
            '<b>but it will take a while to handle for you if there are too many of them,</b>',
            f'<b>each batch will retry up to {BATCH_SIZE} tasks,</b>',
            '<b>now choose an option below and go on.</b>',
        ]),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text='Only download tasks',
                    callback_data=_build_callback_data(LeechFileStatus.DOWNLOAD_FAIL.value, 0),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Only upload tasks',
                    callback_data=_build_callback_data(LeechFileStatus.UPLOAD_FAIL.value, 0),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Both',
                    callback_data=_build_callback_data('both', 0),
                )
            ],
            get_bottom_buttons('', should_have_return=False)
        ])
    )


def _build_callback_data(status: str, offset: int) -> str:
    return f'{COMMAND_PREFIX}{status}:{offset}'


def _parse_status_and_offset(raw: str) -> tuple[str, int]:
    if ':' not in raw:
        return raw, 0
    status, offset = raw.split(':', 1)
    try:
        return status, int(offset)
    except ValueError:
        return status, 0


def _build_continue_markup(status: str, next_offset: int, remaining: int | None) -> InlineKeyboardMarkup | None:
    if remaining is None or remaining <= 0:
        return None
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text='Continue next batch',
                callback_data=_build_callback_data(status, next_offset)
            )
        ],
        get_bottom_buttons('', should_have_return=False)
    ])
