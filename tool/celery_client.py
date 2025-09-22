from celery import Celery
from beans.singleton import Singleton
from config.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD


class CeleryClient(Singleton):
    def __init__(self):
        app = Celery(
            'Celery',
            broker=f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
        )

        app.conf.update(
            task_serializer='pickle',
            result_serializer='pickle',
            accept_content=['pickle']
        )

        self.client = app


celery_client = CeleryClient().client
