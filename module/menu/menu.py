import pyrogram
from tool.utils import is_authorized_user
from pyrogram import filters, Client
from pyrogram.types import BotCommand, Message


@Client.on_message(filters.command('menu') & (filters.private | filters.group | filters.channel) & is_authorized_user)
async def menu(client: Client, message: Message):
    commands = [
        BotCommand(command='leech', description='leech'),
        BotCommand(command='monitor', description='monitor')
    ]
    target_chat_id = message.chat.id

    await client.delete_bot_commands(scope=pyrogram.types.BotCommandScopeChat(chat_id=target_chat_id))
    await client.set_bot_commands(
        commands,
        scope=pyrogram.types.BotCommandScopeChat(chat_id=target_chat_id)
    )
    await message.reply('🎉🎉🎉 Command set up successfully')
