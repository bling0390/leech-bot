import json
import logging
from typing import Any, Optional

from redis import Redis

DEFAULT_TTL_SECONDS = 60 * 60 * 24
logger = logging.getLogger(__name__)


class IdempotencyService:
    def __init__(self, redis_client: Optional[Redis]):
        self.redis = redis_client

    def get(self, key: str) -> Optional[dict[str, Any]]:
        if not self.redis:
            return None
        try:
            cached = self.redis.get(key)
            if not cached:
                return None
            try:
                return json.loads(cached)
            except Exception:
                return {'task_id': cached}
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Idempotency lookup failed: %s', exc, extra={'idempotency_key': key})
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        if not self.redis:
            return
        try:
            self.redis.setex(key, DEFAULT_TTL_SECONDS, json.dumps(value))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Idempotency persistence failed: %s', exc, extra={'idempotency_key': key})

