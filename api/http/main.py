import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.http.constants import HEADER_REQUEST_ID
from api.http.core.errors import AppError, BadRequestError
from api.http.schemas.base import ErrorData, ErrorItem, ErrorResponse
from api.http.routers import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)

app = FastAPI(title='Leech Bot Web API')
app.include_router(api_router)


@app.middleware('http')
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get(HEADER_REQUEST_ID) or str(uuid4())
    response = await call_next(request)
    if HEADER_REQUEST_ID not in response.headers:
        response.headers[HEADER_REQUEST_ID] = request.state.request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, 'request_id', str(uuid4()))
    errors = []
    for item in exc.errors():
        field_path = '.'.join(str(part) for part in item.get('loc', []) if part != 'body')
        errors.append(
            ErrorItem(
                field=field_path or 'body',
                reason=item.get('msg', 'invalid'),
            )
        )
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            code=BadRequestError.code,
            message='Invalid parameter',
            request_id=request_id,
            data=ErrorData(errors=errors),
        ).model_dump(by_alias=True),
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    request_id = getattr(request.state, 'request_id', str(uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
        ).model_dump(by_alias=True),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).error('Unhandled exception', exc_info=exc)
    request_id = getattr(request.state, 'request_id', str(uuid4()))
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code=20000,
            message='Internal error',
            request_id=request_id,
        ).model_dump(by_alias=True),
    )
