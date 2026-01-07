from uuid import uuid4

from fastapi import APIRouter, Request

from api.http.schemas.base import ApiResponse, SchemaBase

router = APIRouter()


class HealthData(SchemaBase):
    status: str


@router.get('/healthz', response_model=ApiResponse)
async def healthz(request: Request):
    request_id = getattr(request.state, 'request_id', None) or str(uuid4())
    return ApiResponse(
        code=0,
        message='success',
        request_id=request_id,
        data=HealthData(status='ok'),
    )
