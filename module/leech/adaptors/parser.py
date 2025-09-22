from loguru import logger
from typing import Callable, TypeAlias
from module.leech.beans.leech_file import LeechFile
from module.leech.utils.adaptor import setup_services

ParseFilter: TypeAlias = Callable[[str], bool]


EXPORT_NAME_PARSE_LINK_FILTER = 'parse_link_filter'
EXPORT_NAME_PARSE_LINK = 'parse_link'

parse_service: dict[ParseFilter, Callable[[str, ...], list[LeechFile]]] = \
    setup_services('module/leech/parsers', EXPORT_NAME_PARSE_LINK_FILTER, EXPORT_NAME_PARSE_LINK)


def execute_parse_link(link: str, **kwargs) -> list[LeechFile]:
    for _filter, func in parse_service.items():
        if _filter(link):
            return func(link, **kwargs)

    logger.warning('Parse service not found.')
    return []
