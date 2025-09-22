import os
import time
import psutil
import prettytable as pt
from pyrogram.types import Message
from pyrogram import filters, Client
from tool.utils import is_admin, convert_bytes
from pyrogram.enums.parse_mode import ParseMode
from config.config import TELEGRAM_ADMIN_ID, BOT_DOWNLOAD_LOCATION

print(psutil.net_io_counters(pernic=True, nowrap=False))

io = psutil.net_io_counters()
prev_bytes_sent = io.bytes_sent
prev_bytes_recv = io.bytes_recv
prev_count_time = int(time.time())


@Client.on_message(filters.command('monitor') & filters.private & is_admin)
async def start(client: Client, message: Message):
    global prev_bytes_sent, prev_bytes_recv, prev_count_time
    ram_usage = psutil.Process(os.getpid()).memory_info().rss
    disk_usage = psutil.disk_usage(BOT_DOWNLOAD_LOCATION)
    cpu_usage_percent = psutil.cpu_percent()
    io_counter = psutil.net_io_counters()

    table = pt.PrettyTable(['Statistic', 'Current'], padding_width=1)
    table.valign['Statistic'] = 'm'
    table.valign['Current'] = 'm'

    table._max_width = {'Statistic': 20, 'Current': 15}

    current_bytes_sent = io_counter.bytes_sent
    current_bytes_recv = io_counter.bytes_recv
    current_count_time = int(time.time())

    print(f'current_bytes_sent: {convert_bytes(current_bytes_sent)}', f'prev_bytes_sent: {convert_bytes(prev_bytes_sent)}', f'current_count_time: {current_count_time - prev_count_time}')
    print(f'current_bytes_recv: {convert_bytes(current_bytes_recv)}', f'prev_bytes_recv: {convert_bytes(prev_bytes_recv)}', f'current_count_time: {current_count_time - prev_count_time}')

    table.add_row(['CPU Usage', f'{cpu_usage_percent}%'], divider=True)
    table.add_row(['RAM Usage', convert_bytes(ram_usage)], divider=True)
    table.add_row(['DISK Used', convert_bytes(disk_usage.used)], divider=True)
    table.add_row(['DISK Free', convert_bytes(disk_usage.free)], divider=True)
    table.add_row(['Inbound', convert_bytes(current_bytes_recv)], divider=True)
    table.add_row(['Outbound', convert_bytes(current_bytes_sent)], divider=True)
    table.add_row([
        'Inbound Speed',
        f'{convert_bytes(int((current_bytes_recv - prev_bytes_recv) / (current_count_time - prev_count_time)))}/s'
    ],
        divider=True
    )
    table.add_row([
        'Outbound Speed',
        f'{convert_bytes(int((current_bytes_sent - prev_bytes_sent) / (current_count_time - prev_count_time)))}/s'
    ],
        divider=True
    )

    prev_bytes_sent = current_bytes_sent
    prev_bytes_recv = current_bytes_recv
    prev_count_time = current_count_time

    m = await client.send_message(
        chat_id=TELEGRAM_ADMIN_ID,
        disable_web_page_preview=True,
        text=f'<pre>{table}</pre>'[:4096],  # 4096 is the maximum length of a message
        parse_mode=ParseMode.HTML
    )

    time.sleep(5)
    await message.delete()
    await m.delete()
