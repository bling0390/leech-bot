from urllib.parse import quote
from celery import Celery
from beans.singleton import Singleton
from config.config import REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD, REDIS_BROKER_URL

class CeleryClient(Singleton):
    def __init__(self):
        broker = (REDIS_BROKER_URL or '').strip()
        if broker == '':
            host = REDIS_HOST or 'localhost'
            port = int(REDIS_PORT or 6379)
            username = (REDIS_USERNAME or '').strip()
            password = REDIS_PASSWORD

            if password is None or str(password) == '':
                broker = f'redis://{host}:{port}/0'
            else:
                password_escaped = quote(str(password), safe='')
                if username == '':
                    broker = f'redis://:{password_escaped}@{host}:{port}/0'
                else:
                    username_escaped = quote(username, safe='')
                    broker = f'redis://{username_escaped}:{password_escaped}@{host}:{port}/0'

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
