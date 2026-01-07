from enum import Enum


HEADER_REQUEST_ID = 'X-REQUEST-ID'
HEADER_IDEMPOTENCY_KEY = 'X-IDEMPOTENCY-KEY'


class ParseStatus(str, Enum):
    QUEUED = 'QUEUED'
