from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_file import LeechFile
from module.leech.utils.bunkr import parse_bunkr_link
from module.leech.decorators.parse import catch_parse_exception, create_document


class Bunkr(IParser):
    def parse_link_filter(self, link: str) -> bool:
        return 'bunkr' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        return parse_bunkr_link(link, **kwargs)


instance = Bunkr()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
