from typing import Any, List, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator

from api.http.constants import ParseStatus
from api.http.schemas.base import ApiResponse, SchemaBase


class LeechRequest(SchemaBase):
    link: str
    target: Optional[str] = None
    path: Optional[str] = None
    tool: Optional[str] = None

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


class LeechResponseData(SchemaBase):
    task_id: str
    status: str = Field(default=ParseStatus.QUEUED)
    files: List[Any]


class LeechSuccessResponse(ApiResponse):
    data: LeechResponseData
