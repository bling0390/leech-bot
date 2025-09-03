import pyrogram
from tool.utils import is_admin
from pyrogram import filters, Client
from config.config import TELEGRAM_ADMIN_ID
from pyrogram.types import BotCommand, Message


@Client.on_message(filters.command('menu') & filters.private & is_admin)
async def menu(client: Client, message: Message):
    commands = [
        BotCommand(command='leech', description='leech'),
        BotCommand(command='monitor', description='monitor'),
        # 磁盘管理统一命令
        BotCommand(command='disk', description='磁盘管理 (status, start, stop, clean, alerts)'),
        # 网络监控统一命令
        BotCommand(command='network', description='网络监控 (status, interfaces, connections, start, stop)'),
        # 保留独立命令以维持向后兼容性
        BotCommand(command='disk_status', description='查看磁盘空间状态'),
        BotCommand(command='disk_monitor', description='磁盘监控开关'),
        BotCommand(command='disk_clean', description='清理下载目录'),
        BotCommand(command='network_status', description='查看网络状态')
    ]

    await client.delete_bot_commands()
    await client.set_bot_commands(
        commands,
        scope=pyrogram.types.BotCommandScopeChat(chat_id=TELEGRAM_ADMIN_ID)
    )
    await message.reply('🎉🎉🎉 Command set up successfully')
