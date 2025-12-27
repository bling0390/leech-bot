from celery import Celery
from beans.singleton import Singleton
from config.config import REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD

class CeleryClient(Singleton):
    def __init__(self):
        if REDIS_PASSWORD is None or str(REDIS_PASSWORD) == '':
            broker = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
        else:
            broker = f'redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'

        app = Celery(
            'Celery',
            broker=broker
        )

        app.conf.update(
            task_serializer='pickle',
            result_serializer='pickle',
            accept_content=['pickle']
        )

        self.client = app


celery_client = CeleryClient().client
