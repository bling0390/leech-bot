import uuid
from pyrogram import Client

from module.leech.beans.leech_file import LeechFile
from tool.telegram_client import get_telegram_client, update_telegram_client
from module.leech.interfaces.uploader import IUploader
from config.config import TELEGRAM_CHANNEL_ID, TELEGRAM_ADMIN_ID, TELEGRAM_BOT_TOKEN, TELEGRAM_API_ID, \
    TELEGRAM_API_HASH, BOT_PROXY_SCHEMAS, BOT_PROXY_HOST, BOT_PROXY_PORT, NODE_ENV
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.constants.leech_file_tool import LeechFileSyncTool
from module.leech.decorators.upload import catch_upload_exception, clean_temp_file, check_before_upload


class Telegram(IUploader):
    def upload_filter(self, sync_tool: str):
        return sync_tool == LeechFileSyncTool.TELEGRAM

    @catch_upload_exception
    @check_before_upload
    @clean_temp_file
    def upload(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        telegram_client = Client(
            f'upload_bot_{str(uuid.uuid4())}',
            proxy={'scheme': BOT_PROXY_SCHEMAS, 'hostname': BOT_PROXY_HOST, 'port': BOT_PROXY_PORT} if all(
                [BOT_PROXY_SCHEMAS, BOT_PROXY_HOST, BOT_PROXY_PORT]) and NODE_ENV != 'PRODUCTION' else None,
            bot_token=TELEGRAM_BOT_TOKEN,
            api_id=TELEGRAM_API_ID,
            api_hash=TELEGRAM_API_HASH
        )

        telegram_client.start()

        telegram_client.send_video(
            chat_id=TELEGRAM_ADMIN_ID,
            video=leech_file.get_full_name(),
            file_name=leech_file.name
        )

        telegram_client.stop()

        leech_file.upload_status = LeechFileStatus.UPLOAD_SUCCESS

        return leech_file


instance = Telegram()
upload_filter = instance.upload_filter
upload = instance.upload
