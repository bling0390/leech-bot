import datetime
from celery import chain
from tool.utils import is_admin
from constants.worker import Queue
from pyrogram import Client, filters
from module.leech.beans.leech_file import LeechFile
from config.config import FAILED_TASK_EXPIRE_AFTER_DAYS
from module.leech.utils.button import get_bottom_buttons
from module.leech.adaptors.uploader import process_upload
from module.leech.utils.message import send_message_to_admin
from module.leech.adaptors.downloader import process_download
from module.leech.constants.leech_file_status import LeechFileStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

COMMAND_PREFIX = 'leech_retry_'
COMMAND_PREFIX_SINGLE = f'{COMMAND_PREFIX}single_'


def retry_specific_tasks(
    filter_status: LeechFileStatus
) -> int:
    leech_files: list[LeechFile] = LeechFile.objects(
        status=filter_status,
        created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)
    ) if filter_status == LeechFileStatus.DOWNLOAD_FAIL else LeechFile.objects(
        upload_status=filter_status,
        created_at__gte=datetime.datetime.utcnow() - datetime.timedelta(days=FAILED_TASK_EXPIRE_AFTER_DAYS)
    )

    for leech_file in leech_files:
        leech_file.status = LeechFileStatus.INITIAL
        leech_file.upload_status = LeechFileStatus.INITIAL
        leech_file.updated_at = datetime.datetime.utcnow()
        leech_file.save()

        create_pending_task(leech_file)

    return len(leech_files)


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

        await send_message_to_admin('✅ <b>Task has retried!</b>')
    else:
        await send_message_to_admin('❌ <b>Task not exist or expired</b>')


@Client.on_callback_query(filters.regex(f'^{COMMAND_PREFIX}'))
async def interact_callback(_, query):
    status = query.data.removeprefix(COMMAND_PREFIX)

    await query.message.delete()

    if status == 'both':
        download_count = retry_specific_tasks(LeechFileStatus.DOWNLOAD_FAIL)
        upload_count = retry_specific_tasks(LeechFileStatus.UPLOAD_FAIL)
        message = f'✅ <b>{download_count + upload_count} tasks has retried!</b>'
    else:
        count = retry_specific_tasks(status)
        message = f'✅ <b>{count} tasks has retried!</b>'

    await send_message_to_admin(message)


def create_pending_task(leech_file: LeechFile):
    chain(
        process_download.signature(
            (leech_file,),
            queue=f'{Queue.FILE_DOWNLOAD_QUEUE}@{leech_file.tool}'
        ),
        process_upload.signature(queue=f'{Queue.FILE_SYNC_QUEUE}@{leech_file.sync_tool}')
    ).apply_async()


@Client.on_message(filters.command('leech retry') & filters.private & is_admin)
async def leech_retry(_: Client, message: Message):
    await message.reply(
        text='\n\n'.join([
            f'<b>Tasks will download/upload again if they are failed within {FAILED_TASK_EXPIRE_AFTER_DAYS} days,</b>',
            '<b>but it will take a while to handle for you if there are too many of them,</b>',
            '<b>now choose an option below and go on.</b>',
        ]),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text='Only download tasks',
                    callback_data=f'{COMMAND_PREFIX}{LeechFileStatus.DOWNLOAD_FAIL}',
                )
            ],
            [
                InlineKeyboardButton(
                    text='Only upload tasks',
                    callback_data=f'{COMMAND_PREFIX}{LeechFileStatus.UPLOAD_FAIL}',
                )
            ],
            [
                InlineKeyboardButton(
                    text='Both',
                    callback_data=f'{COMMAND_PREFIX}both',
                )
            ],
            get_bottom_buttons('', should_have_return=False)
        ])
    )
