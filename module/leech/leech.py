import datetime
import time
import argparse
import threading
from loguru import logger
from pyrogram import filters, Client

from pyrogram.enums.parse_mode import ParseMode
from module.i18n.services.i18n_manager import I18nManager

from beans.setting import Setting
from constants.setting import SettingKey
from module.leech.beans.leech_file import LeechFile
from module.leech.constants.message import MessageStatus
from module.leech.utils.button import get_bottom_buttons, get_upload_tool_buttons, get_alist_storage_buttons, \
    get_rclone_remote_buttons, get_telegram_destination_buttons
from module.leech.beans.leech_message import LeechMessage
from module.leech.beans.leech_prompt_input import LeechPromptInput
from module.leech.constants.leech_file_tool import LeechFileSyncTool, LeechFileTool
from module.leech.constants.leech_prompt_step import LeechPromptStep
from module.leech.constants.leech_file_status import LeechFileStatus
from constants.worker import Hostname, Project, Queue
from module.leech.utils.message import send_message_to_admin
from tool.utils import is_admin, open_celery_worker_process
from tool.telegram_client import get_telegram_client
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, Message)
from module.leech.adaptors.parser import execute_parse_link
from config.config import TELEGRAM_ADMIN_ID, MAXIMUM_LEECH_WORKER, MAXIMUM_SYNC_WORKER, TELEGRAM_CHANNEL_ID

leech_prompt_input = LeechPromptInput()
alist_storages = []
UPLOAD_DESTINATION = 'dest'
UPLOAD_TOOL = 'tool'
leech_message_checker = None
current_upload_setting = {}


def start_polling_messages():
    while True:
        
        for leech_message in LeechMessage.objects(status=MessageStatus.INITIAL).order_by('created_at'):
            try:
                if leech_message.file_status in [
                    LeechFileStatus.UPLOAD_SUCCESS,
                    LeechFileStatus.UPLOAD_FAIL,
                    LeechFileStatus.DOWNLOAD_FAIL,
                    LeechFileStatus.SKIP_DOWNLOAD
                ]:
                    get_telegram_client().send_message(
                        chat_id=TELEGRAM_ADMIN_ID,
                        disable_web_page_preview=True,
                        text=leech_message.content,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton('Retry', callback_data=f'leech_retry_single_{leech_message.file_id}')]
                        ]) if (
                                leech_message.file_status == LeechFileStatus.DOWNLOAD_FAIL or
                                leech_message.file_status == LeechFileStatus.UPLOAD_FAIL
                        ) else None
                    )

                    leech_message.status = MessageStatus.ALREADY_SENT
                else:
                    leech_message.status = MessageStatus.DISCARD

                leech_message.updated_at = datetime.datetime.utcnow()
                leech_message.save()
            except Exception as e:
                logger.error(e)
                pass

        time.sleep(5)


def generate_queue_names(queue_name: str, tool_class: type[LeechFileSyncTool | LeechFileTool]) -> str:
    return ','.join([f'{queue_name}@{tool}' for tool in list(
        map(
            lambda x: x[0],
            filter(
                lambda i: not i[0].startswith('_'),
                vars(tool_class).items()
            )
        )
    )])


def start_celery_process():
    open_celery_worker_process(
        Project.LEECH_DOWNLOADER,
        f'{Hostname.FILE_LEECH_WORKER}@{Queue.FILE_DOWNLOAD_QUEUE}',
        generate_queue_names(Queue.FILE_DOWNLOAD_QUEUE, LeechFileTool),
        MAXIMUM_LEECH_WORKER
    )

    open_celery_worker_process(
        Project.LEECH_UPLOADER,
        f'{Hostname.FILE_SYNC_WORKER}@{Queue.FILE_SYNC_QUEUE}',
        generate_queue_names(Queue.FILE_SYNC_QUEUE, LeechFileSyncTool),
        MAXIMUM_SYNC_WORKER
    )


def use_thread_polling_message():
    global leech_message_checker

    if leech_message_checker is None or not leech_message_checker.is_alive():
        leech_message_checker = threading.Thread(
            daemon=True,
            name='leech_message_checker',
            target=start_polling_messages
        )

        leech_message_checker.start()


use_thread_polling_message()
start_celery_process()


async def get_telegram_destination_markup():
    return await send_message_to_admin(
        content=I18nManager().translate('leech.common.select_destination'),
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(get_telegram_destination_buttons('leech_telegram_dest_'))
    )


async def get_alist_storage_markup():
    global alist_storages

    storage_buttons, alist_storages = await get_alist_storage_buttons('leech_alist_path_')

    return await send_message_to_admin(
        content=I18nManager().translate('leech.common.select_destination'),
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(storage_buttons)
    )


async def get_rclone_remote_markup():
    return await send_message_to_admin(
        content=I18nManager().translate('leech.common.select_destination'),
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(get_rclone_remote_buttons('leech_rclone_remote_'))
    )


async def prepare_download_files():
    leech_files: list[LeechFile] = []

    i18n_manager = I18nManager()
    m = await send_message_to_admin(i18n_manager.translate('leech.common.processing'), False)

    for link in leech_prompt_input.links:
        leech_files.extend(execute_parse_link(
            link,
            sync_tool=(current_upload_setting.get(UPLOAD_TOOL) or leech_prompt_input.sync_tool),
            sync_path=(current_upload_setting.get(UPLOAD_DESTINATION) or leech_prompt_input.storage_path)
        ))

    await m.delete()
    await send_message_to_admin(
        '❌ <b>No task have been created!</b>' if len(
            leech_files) == 0 else f'🎉🎉🎉 <b>{len(leech_files)} tasks have been created!</b>'
    )


async def get_upload_tool_markup():
    tool_buttons: list[list[InlineKeyboardButton]] = get_upload_tool_buttons('leech_sync_')

    if len(tool_buttons) == 0:
        return await send_message_to_admin('❌ <b>No sync tool available</b>', False)

    return await send_message_to_admin(
        content=I18nManager().translate('leech.common.select_destination'),
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(tool_buttons)
    )


async def _next(message: Message, previous_step: LeechPromptStep | None):
    if previous_step is None:
        if not current_upload_setting.get(UPLOAD_TOOL):
            return await get_upload_tool_markup()
        else:
            return await _next(message, LeechPromptStep.show_sync_tool)

    if previous_step == LeechPromptStep.show_sync_tool and (
            leech_prompt_input.sync_tool == LeechFileSyncTool.ALIST or
            current_upload_setting.get(UPLOAD_TOOL) == LeechFileSyncTool.ALIST
    ):
        if not current_upload_setting.get(UPLOAD_DESTINATION):
            return await get_alist_storage_markup()
        else:
            return await _next(message, LeechPromptStep.show_alist_remote_path)

    if previous_step == LeechPromptStep.show_sync_tool and (
            leech_prompt_input.sync_tool == LeechFileSyncTool.RCLONE or
            current_upload_setting.get(UPLOAD_TOOL) == LeechFileSyncTool.RCLONE
    ):
        if not current_upload_setting.get(UPLOAD_DESTINATION):
            return await get_rclone_remote_markup()
        else:
            return await _next(message, LeechPromptStep.show_rclone_remote_path)
            
    if previous_step == LeechPromptStep.show_sync_tool and (
            leech_prompt_input.sync_tool == LeechFileSyncTool.TELEGRAM or
            current_upload_setting.get(UPLOAD_TOOL) == LeechFileSyncTool.TELEGRAM
    ):
        if not current_upload_setting.get(UPLOAD_DESTINATION):
            return await get_telegram_destination_markup()
        else:
            return await _next(message, LeechPromptStep.show_telegram_destination)

    if previous_step == LeechPromptStep.show_rclone_remote_path or \
            previous_step == LeechPromptStep.show_alist_remote_path or \
            previous_step == LeechPromptStep.show_telegram_destination:
        await prepare_download_files()
        use_thread_polling_message()


@Client.on_callback_query(filters.regex('^leech.*(return|close)$'))
async def bottom_menu_callback(_, query):
    if query.data.endswith('close'):
        return await query.message.delete()


@Client.on_message(filters.command('leech') & filters.private & is_admin)
async def start(_: Client, message: Message):
    global current_upload_setting

    try:
        parser = argparse.ArgumentParser(description='Process input arguments.')

        parser.add_argument('links', metavar='link', type=str, nargs='+',
                            help='Download links separated by space.')

        args = parser.parse_args(message.command[1:])
    except (Exception, SystemExit):
        return await message.reply(
            text='\n\n'.join([
                '<b>Available Commands</b>',
                '<b>1./leech monitor</b> - Monitor worker process',
                '<b>2./leech rate</b> - Update worker rate limit',
                '<b>3./leech retry</b> - Retry failed tasks',
                '<b>4./leech setting</b> - Monitor process',
                '<b>5./leech terminate</b> - Terminate pending tasks',
                '<b>6./leech worker</b> - Startup or shutdown worker',
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    current_upload_setting = getattr(Setting.objects(key=SettingKey.FILE_UPLOAD_DESTINATION).first(), 'value', {})
    leech_prompt_input.update_links(args.links)

    await _next(message, previous_step=None)


@Client.on_callback_query(filters.regex('^leech_alist_path_'))
async def path_menu_callback(_, query):
    leech_prompt_input.update_storage_path(
        alist_storages[int(query.data.removeprefix('leech_alist_path_'))]['mount_path']
    )

    await query.message.delete()

    await _next(query.message, previous_step=LeechPromptStep.show_alist_remote_path)


@Client.on_callback_query(filters.regex('^leech_rclone_remote_'))
async def rclone_remote_menu_callback(_, query):
    leech_prompt_input.update_storage_path(query.data.removeprefix('leech_rclone_remote_'))

    await query.message.delete()

    await _next(query.message, previous_step=LeechPromptStep.show_rclone_remote_path)


@Client.on_callback_query(filters.regex('^leech_sync_'))
async def sync_menu_callback(_, query):
    leech_prompt_input.sync_tool = query.data.removeprefix('leech_sync_')

    await query.message.delete()

    await _next(query.message, previous_step=LeechPromptStep.show_sync_tool)


@Client.on_callback_query(filters.regex('^leech_telegram_dest_'))
async def telegram_destination_menu_callback(_, query):
    destination = query.data.removeprefix('leech_telegram_dest_')
    
    # i18n_manager.translate('leech.prompt.destination_selection')
    if destination == 'channel':
        leech_prompt_input.update_storage_path(TELEGRAM_CHANNEL_ID)
    elif destination == 'private':
        leech_prompt_input.update_storage_path(str(query.from_user.id))
    
    await query.message.delete()
    
    await _next(query.message, previous_step=LeechPromptStep.show_telegram_destination)
