import logging
from typing import Any

from celery import Celery

from api.http.core.errors import QueueUnavailable
from api.http.core.settings import Settings

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._celery: Celery | None = None

    def _get_celery(self) -> Celery:
        if self._celery:
            return self._celery

        try:
            from tool.celery_client import celery_client

            self._celery = celery_client
            return self._celery
        except Exception as exc:  # pragma: no cover - fallback path
            logger.warning('Falling back to standalone Celery app: %s', exc)

        self._celery = Celery('leech_webapi', broker=self.settings.celery_broker_url)
        self._celery.conf.update(
            task_serializer='pickle',
            result_serializer='pickle',
            accept_content=['pickle', 'json'],
        )
        return self._celery

    def enqueue(self, payload: dict[str, Any]) -> str:
        try:
            task = self._get_celery().send_task(
                self.settings.celery_task_name,
                args=[payload],
                queue=self.settings.celery_queue,
            )
            logger.info(
                'queue.enqueued',
                extra={
                    'request_id': payload.get('request_id'),
                    'task_id': task.id,
                    'queue': self.settings.celery_queue,
                },
            )
            return task.id
        except Exception as exc:
            logger.error(
                'Failed to enqueue task',
                exc_info=exc,
                extra={
                    'request_id': payload.get('request_id'),
                    'queue': self.settings.celery_queue,
                },
            )
            raise QueueUnavailable('Failed to enqueue task')

