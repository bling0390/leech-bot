from pyrogram import Client
from beans.singleton import Singleton


class TelegramClient(Singleton):
    def __init__(self):
        self.telegram_client = None

    def get_telegram_client(self):
        return self.telegram_client

    def update_telegram_client(self, client: Client):
        self.telegram_client = client


instance = TelegramClient()
get_telegram_client = instance.get_telegram_client
update_telegram_client = instance.update_telegram_client

