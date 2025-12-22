import shutil
import threading
import time
import httpx
from loguru import logger

from config.config import (
    BOT_DOWNLOAD_LOCATION,
    DISK_FREE_THRESHOLD_BYTES,
    TELEGRAM_ADMIN_ID,
    TELEGRAM_BOT_TOKEN
) 
from tool.worker_manager import shutdown_download_workers, start_download_workers
from tool.utils import convert_bytes


TELEGRAM_API_BASE = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'


class DiskSpaceMonitor:
    def __init__(self):
        self.disk_threshold = max(0, DISK_FREE_THRESHOLD_BYTES)
        self.low_space = False
        self.monitor_thread = None
        self.download_workers_paused = False

    def start(self):
        if self.disk_threshold == 0:
            logger.info('Disk space monitor disabled (threshold set to 0).')
            return

        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self._loop, daemon=True, name='disk_space_monitor')
            self.monitor_thread.start()

    def _loop(self):
        while True:
            free_bytes = self._get_free_space()

            if free_bytes is None:
                time.sleep(30)
                continue

            if free_bytes <= self.disk_threshold and not self.low_space:
                self.low_space = True
                self._handle_low_space(free_bytes)
            elif free_bytes > self.disk_threshold and self.low_space:
                self.low_space = False
                self._handle_recovery(free_bytes)

            interval = self._calculate_interval(free_bytes)
            time.sleep(interval)

    def _get_free_space(self):
        try:
            usage = shutil.disk_usage(BOT_DOWNLOAD_LOCATION or '.')
            return usage.free
        except FileNotFoundError:
            logger.warning('Download directory "%s" not found when checking disk usage.', BOT_DOWNLOAD_LOCATION)
            return None
        except Exception as exc:
            logger.error('Failed to fetch disk usage: %s', str(exc))
            return None

    def _calculate_interval(self, free_bytes: int | None) -> int:
        if free_bytes is None:
            return 30

        if free_bytes <= self.disk_threshold:
            return 5
        elif free_bytes <= self.disk_threshold * 2:
            return 10
        else:
            return 30

    def _handle_low_space(self, free_bytes: int):
        paused_workers = shutdown_download_workers()
        self.download_workers_paused = len(paused_workers) > 0

        message = '\n'.join([
            '⚠️ <b>Disk space is running low!</b>',
            f'Current free space: {convert_bytes(free_bytes)}',
            'All download workers have been paused. Please clean up the download directory '
            'or wait for upload tasks to free more space.'
        ])

        self._send_admin_message(message)

    def _handle_recovery(self, free_bytes: int):
        if self.download_workers_paused:
            start_download_workers()
            self.download_workers_paused = False

            message = '\n'.join([
                '✅ <b>Disk space recovered.</b>',
                f'Current free space: {convert_bytes(free_bytes)}',
                'Download workers have been resumed and pending tasks will continue automatically.'
            ])
        else:
            message = '\n'.join([
                'ℹ️ <b>Disk space recovery detected.</b>',
                f'Current free space: {convert_bytes(free_bytes)}'
            ])

        self._send_admin_message(message)

    def _send_admin_message(self, text: str):
        if TELEGRAM_BOT_TOKEN == '' or TELEGRAM_ADMIN_ID == -1:
            logger.warning('Unable to send disk notification because Telegram credentials are missing.')
            return

        try:
            httpx.post(
                f'{TELEGRAM_API_BASE}/sendMessage',
                json={
                    'chat_id': TELEGRAM_ADMIN_ID,
                    'text': text,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': True
                },
                timeout=10.0
            ).raise_for_status()
        except Exception as exc:
            logger.error('Failed to send disk notification: %s', str(exc))


_monitor = DiskSpaceMonitor()


def start_disk_monitor():
    _monitor.start()
