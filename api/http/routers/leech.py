import logging
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from redis import Redis

from api.http.constants import HEADER_IDEMPOTENCY_KEY, HEADER_REQUEST_ID, ParseStatus
from api.http.core.security import api_key_auth
from api.http.core.settings import Settings, get_settings
from api.http.deps import get_redis_client
from api.http.schemas.base import ErrorResponse
from api.http.schemas.leech import LeechRequest, LeechResponseData, LeechSuccessResponse
from api.http.services.idem_service import IdempotencyService
from api.http.services.parse_service import parse_link, serialize_files
from api.http.services.queue_service import QueueService

router = APIRouter(prefix='', tags=['leech'])
logger = logging.getLogger(__name__)


@router.post(
    '/leech',
    response_model=LeechSuccessResponse,
    responses={
        400: {'model': ErrorResponse},
        401: {'model': ErrorResponse},
        500: {'model': ErrorResponse},
        503: {'model': ErrorResponse},
    },
    dependencies=[Depends(api_key_auth)],
)
async def leech_endpoint(
    payload: LeechRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    redis_client: Optional[Redis] = Depends(get_redis_client),
):
    request_id = request.headers.get(HEADER_REQUEST_ID) or getattr(request.state, 'request_id', None) or str(uuid4())
    idempotency_key = request.headers.get(HEADER_IDEMPOTENCY_KEY)
    idem_service = IdempotencyService(redis_client)

    if idempotency_key:
        cached = idem_service.get(idempotency_key)
        if cached and cached.get('task_id'):
            task_id = cached['task_id']
            files = cached.get('files', [])
            logger.info(
                'idempotency.hit',
                extra={
                    'request_id': request_id,
                    'idempotency_key': idempotency_key,
                    'task_id': task_id,
                    'file_count': len(files) if isinstance(files, list) else 0,
                },
            )
            return LeechSuccessResponse(
                code=0,
                message='success',
                request_id=request_id,
                data=LeechResponseData(
                    task_id=task_id,
                    status=ParseStatus.QUEUED,
                    files=files if isinstance(files, list) else [],
                ),
            )

    parse_options: dict[str, Any] = payload.model_dump(exclude_none=True)
    parse_options.pop('link', None)
    parse_options['request_id'] = request_id

    files = parse_link(payload.link, request_id, parse_options)
    serialized_files = serialize_files(files)

    queue_payload = {
        'request_id': request_id,
        'link': payload.link,
        'target': payload.target,
        'path': payload.path,
        'tool': payload.tool,
        'files': serialized_files,
    }

    queue_service = QueueService(settings)
    task_id = queue_service.enqueue(queue_payload)

    if idempotency_key:
        idem_service.set(
            idempotency_key,
            {
                'task_id': task_id,
                'files': serialized_files,
            },
        )

    logger.info(
        'leech.enqueued',
        extra={
            'request_id': request_id,
            'link': payload.link,
            'task_id': task_id,
            'file_count': len(serialized_files),
        },
    )

    return LeechSuccessResponse(
        code=0,
        message='success',
        request_id=request_id,
        data=LeechResponseData(
            task_id=task_id,
            status=ParseStatus.QUEUED,
            files=serialized_files,
        ),
    )
