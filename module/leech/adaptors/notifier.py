import datetime
from loguru import logger

import httpx
from celery.apps.worker import Worker
from celery.utils.dispatch import Signal
from celery.worker.consumer import Consumer
from celery.signals import worker_shutdown, celeryd_after_setup, worker_ready

from config.config import TELEGRAM_ADMIN_ID, TELEGRAM_BOT_TOKEN
from constants.worker import WorkerStatus
from module.leech.beans.leech_message import LeechMessage
from module.leech.constants.message import MessageStatus
from module.leech.constants.leech_file_status import LeechFileStatus
from tool.mongo_client import EstablishConnection as EstablishMongodbConnection
from tool.celery_client import celery_client
from tool.worker import celeryd_setup_callback, update_worker_status

EstablishMongodbConnection()

TELEGRAM_API_BASE = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

NOTIFIABLE_STATUSES = {
    LeechFileStatus.UPLOAD_SUCCESS,
    LeechFileStatus.UPLOAD_FAIL,
    LeechFileStatus.DOWNLOAD_FAIL,
    LeechFileStatus.SKIP_DOWNLOAD
}


def _resolve_chat_id(receiver: str | None) -> int:
    target = receiver or TELEGRAM_ADMIN_ID
    try:
        return int(target)
    except (TypeError, ValueError):
        return TELEGRAM_ADMIN_ID


def _build_reply_markup(file_status: LeechFileStatus, file_id: str) -> dict | None:
    if file_status in (LeechFileStatus.DOWNLOAD_FAIL, LeechFileStatus.UPLOAD_FAIL):
        return {
            'inline_keyboard': [[{'text': 'Retry', 'callback_data': f'leech_retry_single_{file_id}'}]]
        }

    return None


@celery_client.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def process_notification(self, message_id: str):
    leech_message: LeechMessage | None = LeechMessage.objects(
        id=message_id,
        status=MessageStatus.INITIAL
    ).first()

    if leech_message is None:
        return

    if leech_message.file_status not in NOTIFIABLE_STATUSES:
        leech_message.status = MessageStatus.DISCARD
        leech_message.updated_at = datetime.datetime.utcnow()
        leech_message.save()
        return

    payload = {
        'chat_id': _resolve_chat_id(leech_message.receiver),
        'text': leech_message.content[:4096],
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }

    reply_markup = _build_reply_markup(leech_message.file_status, leech_message.file_id)

    if reply_markup is not None:
        payload['reply_markup'] = reply_markup

    response = httpx.post(f'{TELEGRAM_API_BASE}/sendMessage', json=payload)
    response.raise_for_status()
    data = response.json()

    if not data.get('ok', False):
        logger.error('Failed to notify user: {}', data)
        raise Exception('Failed to deliver telegram notification.')

    leech_message.status = MessageStatus.ALREADY_SENT
    leech_message.updated_at = datetime.datetime.utcnow()
    leech_message.save()


@celeryd_after_setup.connect
def on_notify_celeryd_setup(sender: str, instance: Worker, **kwargs):
    celeryd_setup_callback(sender, instance, **kwargs)


@worker_ready.connect
def on_notify_worker_ready(signal: Signal, sender: Consumer, **kwargs):
    update_worker_status(sender.hostname, WorkerStatus.READY)


@worker_shutdown.connect
def on_notify_worker_shutdown(signal: Signal, sender: Worker, **kwargs):
    update_worker_status(sender.hostname, WorkerStatus.SHUTDOWN)
