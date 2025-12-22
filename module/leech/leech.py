import argparse
from pyrogram import filters, Client

from pyrogram.enums.parse_mode import ParseMode

from beans.setting import Setting
from constants.setting import SettingKey
from module.leech.beans.leech_file import LeechFile
from module.leech.utils.button import get_bottom_buttons, get_upload_tool_buttons, get_alist_storage_buttons, \
    get_rclone_remote_buttons, get_telegram_destination_buttons
from module.leech.beans.leech_prompt_input import LeechPromptInput
from module.leech.constants.leech_file_tool import LeechFileSyncTool
from module.leech.constants.leech_prompt_step import LeechPromptStep
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.utils.message import send_message_to_admin
from tool.utils import is_authorized_user
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, Message)
from module.leech.adaptors.parser import execute_parse_link
from config.config import TELEGRAM_ADMIN_ID, TELEGRAM_CHANNEL_ID
from tool.worker_manager import start_download_workers, start_upload_workers, start_notify_workers
from tool.disk_monitor import start_disk_monitor

leech_prompt_input = LeechPromptInput()
alist_storages = []
UPLOAD_DESTINATION = 'dest'
UPLOAD_TOOL = 'tool'
current_upload_setting = {}


start_download_workers()
start_upload_workers()
start_notify_workers()
start_disk_monitor()


async def get_telegram_destination_markup(chat_id: int):
    return await send_message_to_admin(
        content='Select Telegram destination',
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(get_telegram_destination_buttons('leech_telegram_dest_')),
        chat_id=chat_id
    )


async def get_alist_storage_markup(chat_id: int):
    global alist_storages

    storage_buttons, alist_storages = await get_alist_storage_buttons('leech_alist_path_')

    return await send_message_to_admin(
        content='Select alist storage',
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(storage_buttons),
        chat_id=chat_id
    )


async def get_rclone_remote_markup(chat_id: int):
    return await send_message_to_admin(
        content='Select rclone remote',
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(get_rclone_remote_buttons('leech_rclone_remote_')),
        chat_id=chat_id
    )


async def prepare_download_files(chat_id: int):
    leech_files: list[LeechFile] = []

    m = await send_message_to_admin('⏳ Parsing links, please wait...', False, chat_id=chat_id)

    for link in leech_prompt_input.links:
        leech_files.extend(execute_parse_link(
            link,
            sync_tool=(current_upload_setting.get(UPLOAD_TOOL) or leech_prompt_input.sync_tool),
            sync_path=(current_upload_setting.get(UPLOAD_DESTINATION) or leech_prompt_input.storage_path),
            request_chat_id=chat_id
        ))

    await m.delete()
    await send_message_to_admin(
        '❌ <b>No task have been created!</b>' if len(
            leech_files) == 0 else f'🎉🎉🎉 <b>{len(leech_files)} tasks have been created!</b>',
        chat_id=chat_id
    )


async def get_upload_tool_markup(chat_id: int):
    tool_buttons: list[list[InlineKeyboardButton]] = get_upload_tool_buttons('leech_sync_')

    if len(tool_buttons) == 0:
        return await send_message_to_admin('❌ <b>No sync tool available</b>', False, chat_id=chat_id)

    return await send_message_to_admin(
        content='Select sync tool',
        should_auto_delete=False,
        delete_after_seconds=-1,
        reply_markup=InlineKeyboardMarkup(tool_buttons),
        chat_id=chat_id
    )


async def _next(message: Message, previous_step: LeechPromptStep | None):
    chat_id = getattr(message.chat, 'id', TELEGRAM_ADMIN_ID)

    if previous_step is None:
        if not current_upload_setting.get(UPLOAD_TOOL):
            return await get_upload_tool_markup(chat_id)
        else:
            return await _next(message, LeechPromptStep.show_sync_tool)

    if previous_step == LeechPromptStep.show_sync_tool and (
            leech_prompt_input.sync_tool == LeechFileSyncTool.ALIST or
            current_upload_setting.get(UPLOAD_TOOL) == LeechFileSyncTool.ALIST
    ):
        if not current_upload_setting.get(UPLOAD_DESTINATION):
            return await get_alist_storage_markup(chat_id)
        else:
            return await _next(message, LeechPromptStep.show_alist_remote_path)

    if previous_step == LeechPromptStep.show_sync_tool and (
            leech_prompt_input.sync_tool == LeechFileSyncTool.RCLONE or
            current_upload_setting.get(UPLOAD_TOOL) == LeechFileSyncTool.RCLONE
    ):
        if not current_upload_setting.get(UPLOAD_DESTINATION):
            return await get_rclone_remote_markup(chat_id)
        else:
            return await _next(message, LeechPromptStep.show_rclone_remote_path)
            
    if previous_step == LeechPromptStep.show_sync_tool and (
            leech_prompt_input.sync_tool == LeechFileSyncTool.TELEGRAM or
            current_upload_setting.get(UPLOAD_TOOL) == LeechFileSyncTool.TELEGRAM
    ):
        if not current_upload_setting.get(UPLOAD_DESTINATION):
            return await get_telegram_destination_markup(chat_id)
        else:
            return await _next(message, LeechPromptStep.show_telegram_destination)

    if previous_step == LeechPromptStep.show_rclone_remote_path or \
            previous_step == LeechPromptStep.show_alist_remote_path or \
            previous_step == LeechPromptStep.show_telegram_destination:
        await prepare_download_files(chat_id)
        use_thread_polling_message()


@Client.on_callback_query(filters.regex('^leech.*(return|close)$'))
async def bottom_menu_callback(_, query):
    if query.data.endswith('close'):
        return await query.message.delete()


@Client.on_message(filters.command('leech') & (filters.private | filters.group | filters.channel) & is_authorized_user)
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
                                                                                                                                              
    # 根据用户选择设置目标ID
    if destination == 'channel':
        leech_prompt_input.update_storage_path(TELEGRAM_CHANNEL_ID)
    elif destination == 'private':
        leech_prompt_input.update_storage_path(str(query.from_user.id))
    
    await query.message.delete()
    
    await _next(query.message, previous_step=LeechPromptStep.show_telegram_destination)
