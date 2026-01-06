import logging
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: Optional[str] = Field(default=None, alias='API_KEY')
    celery_task_name: str = Field(default='tasks.download', alias='CELERY_TASK_NAME')
    celery_queue: str = Field(default='download', alias='CELERY_QUEUE')
    celery_broker_url: str = Field(default='redis://redis:6379/0', alias='CELERY_BROKER_URL')
    redis_url: Optional[str] = Field(default=None, alias='REDIS_URL')

    model_config = SettingsConfigDict(env_file=None, extra='ignore', case_sensitive=False)

    @property
    def redis_dsn(self) -> str:
        if self.redis_url:
            return self.redis_url

        try:
            from config.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

            if REDIS_HOST:
                password = f':{REDIS_PASSWORD}@' if REDIS_PASSWORD else ''
                return f'redis://{password}{REDIS_HOST}:{REDIS_PORT}/0'
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).debug('Failed to load redis config from config.config: %s', exc)

        if self.celery_broker_url.startswith('redis://'):
            return self.celery_broker_url

        return 'redis://redis:6379/0'


@lru_cache
def get_settings() -> Settings:
    return Settings()

