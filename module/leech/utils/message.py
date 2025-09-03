import time
import prettytable as pt
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from config.config import TELEGRAM_ADMIN_ID
from module.leech.beans.leech_file import LeechFile
from tool.telegram_client import get_telegram_client
from tool.utils import convert_bytes


async def send_message_to_admin(
        content: str,
        should_auto_delete: bool = True,
        delete_after_seconds: int = 5,
        **kwargs
) -> Message:
    m = await get_telegram_client().send_message(
        chat_id=TELEGRAM_ADMIN_ID,
        disable_web_page_preview=True,
        text=content[:4096],
        parse_mode=ParseMode.HTML,
        **kwargs
    )

    if should_auto_delete:
        time.sleep(delete_after_seconds)
        await m.delete()

    return m


def format_result_message(**kwargs):
    table = pt.PrettyTable(['Item'])
    table.border = False
    table.preserve_internal_border = True
    table.header = False
    table._min_width = {'Item': 35}
    table._max_width = {'Item': 35}
    table.valign['Item'] = 'm'
    table.align['Item'] = 'l'

    table.add_row(['  '], divider=True)

    table.add_row([f'File name: {kwargs.get("name")}'], divider=True)

    if kwargs.get('is_success', False):
        table.add_row([f'File size: {convert_bytes(int(kwargs.get("size") or "0"))}'], divider=True)
        table.add_row([f'Task status: Done'], divider=True)
    else:
        table.add_row([f'Task phase: {kwargs.get("phase")}'], divider=True)
        table.add_row([f'Task status: {kwargs.get("status")}'], divider=True)
        table.add_row([f'Reason: {kwargs.get("reason")}'[:3072]], divider=True)

    table.add_row(['  '], divider=True)

    return f'<pre>{table.get_string()}</pre>'
