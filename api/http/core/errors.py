from typing import Optional


class AppError(Exception):
    code: int = 20000
    status_code: int = 500
    default_message: str = 'Internal error'

    def __init__(self, message: Optional[str] = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class ParseFailed(AppError):
    code = 10001
    status_code = 400
    default_message = 'Failed to parse link'


class QueueUnavailable(AppError):
    code = 20000
    status_code = 503
    default_message = 'Service unavailable'


class UnauthorizedError(AppError):
    code = 10002
    status_code = 401
    default_message = 'Unauthorized'


class BadRequestError(AppError):
    code = 10001
    status_code = 400
    default_message = 'Invalid parameter'
