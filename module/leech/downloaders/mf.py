from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.downloader import IDownloader
from module.leech.constants.leech_file_tool import LeechFileTool
from module.leech.decorators.download import check_before_download, write_file, check_after_download, move_file, \
    catch_download_exception


class Mediafire(IDownloader):
    def download_filter(self, leech_file: LeechFile) -> bool:
        return leech_file.tool == LeechFileTool.MEDIAFIRE

    @catch_download_exception
    @check_before_download
    @write_file
    @check_after_download
    @move_file
    def download(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        return leech_file


instance = Mediafire()

download_filter = instance.download_filter
download = instance.download
