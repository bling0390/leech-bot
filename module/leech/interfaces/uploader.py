from abc import ABCMeta, abstractmethod
from module.leech.beans.leech_file import LeechFile


class IUploader(metaclass=ABCMeta):
    @abstractmethod
    def upload_filter(self, sync_tool: str):
        pass

    @abstractmethod
    def upload(self, leech_file: LeechFile, *args, **kwargs) -> LeechFile:
        pass


