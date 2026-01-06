import logging
from typing import Any, Iterable, List

from fastapi.encoders import jsonable_encoder

from api.http.core.errors import ParseFailed
from module.leech.adaptors.parser import execute_parse_link

try:  # pragma: no cover - optional dependency helper
    from mongoengine import Document
except Exception:  # pragma: no cover
    Document = None  # type: ignore

logger = logging.getLogger(__name__)


def _ensure_list(files: Any) -> List[Any]:
    if files is None:
        return []
    if isinstance(files, list):
        return files
    if isinstance(files, Iterable) and not isinstance(files, (str, bytes)):
        return list(files)
    return [files]


def serialize_files(files: List[Any]) -> List[Any]:
    serialized: List[Any] = []
    for item in files:
        if Document is not None and isinstance(item, Document):
            try:
                data = item.to_mongo().to_dict()
                if 'id' not in data and getattr(item, 'id', None):
                    data['id'] = str(getattr(item, 'id'))
                serialized.append(data)
                continue
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug('Failed to serialize document: %s', exc)
        serialized.append(jsonable_encoder(item))
    return serialized


def parse_link(link: str, request_id: str, options: dict[str, Any]) -> List[Any]:
    files = _ensure_list(execute_parse_link(link, **options))
    logger.info(
        'parse.completed',
        extra={
            'request_id': request_id,
            'link': link,
            'file_count': len(files),
        },
    )

    if len(files) == 0:
        raise ParseFailed('Failed to parse link')

    return files

