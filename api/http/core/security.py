import logging
from fastapi import Depends, Header

from api.http.core.errors import UnauthorizedError
from api.http.core.settings import Settings, get_settings


async def api_key_auth(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
):
    if settings.api_key and x_api_key != settings.api_key:
        logging.getLogger(__name__).warning('API key mismatch')
        raise UnauthorizedError('Invalid API key')

