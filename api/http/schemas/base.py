from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(value: str) -> str:
    parts = value.split('_')
    return parts[0] + ''.join(part.title() for part in parts[1:])


class SchemaBase(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
    )


class ErrorItem(SchemaBase):
    field: str
    reason: str


class ErrorData(SchemaBase):
    errors: List[ErrorItem] = Field(default_factory=list)


class ApiResponse(SchemaBase):
    code: int = 0
    message: str = 'success'
    request_id: str = Field(..., alias='requestId')
    data: Optional[Any] = None


class ErrorResponse(ApiResponse):
    data: Optional[ErrorData] = None
