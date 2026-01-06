import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.http.core.errors import AppError, BadRequestError
from api.http.routers import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)

app = FastAPI(title='Leech Bot Web API')
app.include_router(api_router)


@app.middleware('http')
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    if 'X-Request-ID' not in response.headers:
        response.headers['X-Request-ID'] = request.state.request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, 'request_id', str(uuid4()))
    return JSONResponse(
        status_code=400,
        content={
            'request_id': request_id,
            'error': {
                'code': BadRequestError.code,
                'message': str(exc.errors()),
            },
        },
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    request_id = getattr(request.state, 'request_id', str(uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'request_id': request_id,
            'error': {
                'code': exc.code,
                'message': exc.message,
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).error('Unhandled exception', exc_info=exc)
    request_id = getattr(request.state, 'request_id', str(uuid4()))
    return JSONResponse(
        status_code=500,
        content={
            'request_id': request_id,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error',
            },
        },
    )
