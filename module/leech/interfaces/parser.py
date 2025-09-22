from abc import ABCMeta, abstractmethod
from module.leech.beans.leech_file import LeechFile


class IParser(metaclass=ABCMeta):
    @abstractmethod
    def parse_link_filter(self, link: str) -> bool:
        pass

    @abstractmethod
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        pass


