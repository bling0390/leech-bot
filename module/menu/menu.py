import pyrogram
from tool.utils import is_admin
from pyrogram import filters, Client
from config.config import TELEGRAM_ADMIN_ID
from pyrogram.types import BotCommand, Message


@Client.on_message(filters.command('menu') & filters.private & is_admin)
async def menu(client: Client, message: Message):
    commands = [
        BotCommand(command='leech', description='leech'),
        BotCommand(command='monitor', description='monitor')
    ]

    await client.delete_bot_commands()
    await client.set_bot_commands(
        commands,
        scope=pyrogram.types.BotCommandScopeChat(chat_id=TELEGRAM_ADMIN_ID)
    )
    await message.reply('🎉🎉🎉 Command set up successfully')
