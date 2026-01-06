from typing import Optional


class AppError(Exception):
    code: str = 'INTERNAL_ERROR'
    status_code: int = 500

    def __init__(self, message: Optional[str] = None):
        super().__init__(message or self.code)
        self.message = message or self.code


class ParseFailed(AppError):
    code = 'PARSE_FAILED'
    status_code = 400


class QueueUnavailable(AppError):
    code = 'QUEUE_UNAVAILABLE'
    status_code = 503


class UnauthorizedError(AppError):
    code = 'UNAUTHORIZED'
    status_code = 401


class BadRequestError(AppError):
    code = 'BAD_REQUEST'
    status_code = 400

