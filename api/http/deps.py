import logging
from typing import Optional

from fastapi import Depends
from redis import Redis

from api.http.core.settings import Settings, get_settings


def get_redis_client(settings: Settings = Depends(get_settings)) -> Optional[Redis]:
    try:
        return Redis.from_url(settings.redis_dsn, decode_responses=True)
    except Exception as exc:  # pragma: no cover - defensive
        logging.getLogger(__name__).warning('Failed to init redis client: %s', exc)
        return None

