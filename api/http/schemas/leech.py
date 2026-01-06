from typing import Any, List, Optional
from uuid import UUID
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class LeechRequest(BaseModel):
    link: str
    target: Optional[str] = None
    path: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    dry_run: Optional[bool] = None

    @field_validator('link')
    @classmethod
    def validate_link(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError('link is required')
        if len(value) > 4096:
            raise ValueError('link is too long')
        parsed = urlparse(value)
        if parsed.scheme.lower() not in {'http', 'https', 'magnet'}:
            raise ValueError('unsupported link scheme')
        return value


class LeechSuccessResponse(BaseModel):
    request_id: UUID
    task_id: str
    status: str = Field(default='queued')
    files: List[Any]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    request_id: UUID
    error: ErrorDetail

