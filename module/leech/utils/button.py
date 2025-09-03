import httpx
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# 可选导入 rclone_python
try:
    from rclone_python import rclone
    RCLONE_AVAILABLE = True
except ImportError:
    rclone = None
    RCLONE_AVAILABLE = False

from api.alist_api import AListAPI
from config.config import RCLONE_REMOTES, TELEGRAM_CHANNEL_ID
from module.leech.constants.leech_file_tool import LeechFileSyncTool
from config.availability import is_alist_available


def get_bottom_buttons(
    callback_prefix: str,
    should_have_return=True,
    should_have_close=True
) -> list[InlineKeyboardButton]:
    buttons = []

    if should_have_return:
        buttons.append(InlineKeyboardButton('↩️ Return', callback_data=f'{callback_prefix}return'))

    if should_have_close:
        buttons.append(InlineKeyboardButton('❌ Close', callback_data=f'{callback_prefix}close'))

    return buttons


def get_upload_tool_buttons(callback_prefix: str) -> list[list[InlineKeyboardButton]]:
    return list(filter(lambda x: x is not None, [
        [
            InlineKeyboardButton(
                text=str(LeechFileSyncTool.ALIST),
                callback_data=f'{callback_prefix}{LeechFileSyncTool.ALIST}',
            )
        ] if is_alist_available() else None,
        [
            InlineKeyboardButton(
                text=str(LeechFileSyncTool.RCLONE),
                callback_data=f'{callback_prefix}{LeechFileSyncTool.RCLONE}',
            )
        ] if RCLONE_AVAILABLE and rclone.is_installed() else None,
        [
            InlineKeyboardButton(
                text=str(LeechFileSyncTool.TELEGRAM),
                callback_data=f'{callback_prefix}{LeechFileSyncTool.TELEGRAM}',
            )
        ]
    ]))


async def get_alist_storage_buttons(callback_prefix: str) -> (list[list[InlineKeyboardButton]], list[any]):
    buttons = []
    storages = []

    try:
        storages = (await AListAPI.get_storages())['data']['content']

        for index in range(len(storages)):
            buttons.append([
                InlineKeyboardButton(
                    text=storages[index]['mount_path'],
                    callback_data=f'{callback_prefix}{str(index)}',
                )
            ])
    except httpx.HTTPError as exc:
        logger.error(exc)

    return buttons, storages


def get_rclone_remote_buttons(callback_prefix: str) -> list[list[InlineKeyboardButton]]:
    return list(map(lambda x: [
        InlineKeyboardButton(
            text=x,
            callback_data=f'{callback_prefix}{x}',
        )
    ], RCLONE_REMOTES))


def get_telegram_destination_buttons(callback_prefix: str) -> list[list[InlineKeyboardButton]]:
    buttons = []
    
    # 添加默认频道按钮
    if TELEGRAM_CHANNEL_ID:
        buttons.append([
            InlineKeyboardButton(
                text="Channel",
                callback_data=f'{callback_prefix}channel',
            )
        ])
    
    # 添加私聊按钮
    buttons.append([
        InlineKeyboardButton(
            text="Private Chat",  # TODO: Add i18n support
            callback_data=f'{callback_prefix}private',
        )
    ])
    
    return buttons
