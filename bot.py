import os
import re
import i18n
import time
import datetime
import platform
import asyncio
from loguru import logger
from pyrogram import Client, idle
from pyrogram.enums import ParseMode
from rclone_python import rclone
from tool.config_utils import is_alist_available
from rclone_python.remote_types import RemoteTypes
from tool.telegram_client import update_telegram_client
from tool.mongo_client import EstablishConnection as EstablishMongodbConnection
from module.disk.auto_start import start_disk_monitor_if_enabled
# Import network module to register command handlers
import module.network.commands.network_monitor
# Import i18n module to register command handlers
import module.i18n.commands.lang_command
from config.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_BOT_TOKEN,
    BOT_LOGS_LOCATION,
    BOT_PROXY_SCHEMAS,
    BOT_PROXY_PORT,
    BOT_PROXY_HOST,
    TELEGRAM_ADMIN_ID,
    TELEGRAM_MEMBER,
    TELEGRAM_CHANNEL_ID,
    RCLONE_REMOTES,
    RCLONE_115_COOKIE,
    MEGA_AUTHORIZATION_EMAIL,
    MEGA_AUTHORIZATION_PASSWORD,
    NODE_ENV
)


def setup_locale():
    i18n.load_path.append('/locales')


def setup_timezone():
    if platform.system() != "Windows":
        os.environ["TZ"] = "Asia/Shanghai"
        time.tzset()


def setup_logger():
    logger.add(
        f'{BOT_LOGS_LOCATION if BOT_LOGS_LOCATION is not None else "logs"}/{datetime.date.today()}.log',
        rotation="5 MB"
    )


async def setup_disk_monitor():
    """设置磁盘监控"""
    try:
        await start_disk_monitor_if_enabled()
        logger.info("磁盘监控设置完成")
    except Exception as e:
        logger.error(f"设置磁盘监控时发生错误: {e}")


def startup():
    logger.success('🎉🎉🎉 Leech bot started!')

    app = Client(
        'bot',
        proxy={'scheme': BOT_PROXY_SCHEMAS, 'hostname': BOT_PROXY_HOST, 'port': BOT_PROXY_PORT} if all(
            [BOT_PROXY_SCHEMAS, BOT_PROXY_HOST, BOT_PROXY_PORT]) and NODE_ENV != 'PRODUCTION' else None,
        bot_token=TELEGRAM_BOT_TOKEN,
        api_id=TELEGRAM_API_ID,
        api_hash=TELEGRAM_API_HASH,
        plugins=dict(root='module'),
        lang_code='zh',
    )
    update_telegram_client(app)
    
    # 当Bot开始运行时启动磁盘监控
    app.set_parse_mode(ParseMode.HTML)
    app.start()
    
    # 在启动后设置磁盘监控 - 使用事件循环正确调度协程
    # 获取当前事件循环并调度磁盘监控设置
    loop = asyncio.get_event_loop()
    loop.create_task(setup_disk_monitor())
    
    idle()


def check_environment_variables():
    if not all(
        [
            TELEGRAM_ADMIN_ID,
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH,
            TELEGRAM_CHANNEL_ID
        ]
    ):
        raise Exception('Telegram environment variables not set, bot will not work as expected.')

    if not is_alist_available():
        logger.warning('AList environment variables not set, bot will not work as expected.')

    if not rclone.is_installed():
        logger.warning('Rclone is not installed, bot will not work as expected.')


def setup_rclone():
    if RemoteTypes.mega in RCLONE_REMOTES and not rclone.check_remote_existing(str(RemoteTypes.mega)):
        rclone.create_remote(
            str(RemoteTypes.mega),
            RemoteTypes.mega,
            user=MEGA_AUTHORIZATION_EMAIL,
            passw=MEGA_AUTHORIZATION_PASSWORD
        )

    if '115' in RCLONE_REMOTES and not rclone.check_remote_existing('115'):
        rclone.create_remote(
            '115',
            '115',
            cookie=RCLONE_115_COOKIE
        )


def setup_mongo():
    EstablishMongodbConnection()


if __name__ == '__main__':
    check_environment_variables()
    setup_timezone()
    setup_logger()
    setup_locale()
    setup_rclone()
    setup_mongo()
    startup()
