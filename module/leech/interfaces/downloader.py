from abc import ABCMeta, abstractmethod
from module.leech.beans.leech_file import LeechFile


class IDownloader(metaclass=ABCMeta):
    @abstractmethod
    def download_filter(self, leech_file: LeechFile) -> bool:
        pass

    @abstractmethod
    def download(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        pass


