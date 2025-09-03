import datetime
from rclone_python import rclone

from module.leech.interfaces.uploader import IUploader
from module.leech.beans.leech_file import LeechFile
from config.config import SHOULD_USE_DATETIME_CATEGORY
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.constants.leech_file_tool import LeechFileSyncTool
from module.leech.decorators.upload import catch_upload_exception, clean_temp_file, check_before_upload


class RClone(IUploader):
    def upload_filter(self, sync_tool: str):
        return sync_tool == LeechFileSyncTool.RCLONE

    @catch_upload_exception
    @check_before_upload
    @clean_temp_file
    def upload(self, leech_file: LeechFile, **kwargs) -> LeechFile:
        rclone.copyto(
            leech_file.get_full_name(),
            f'{leech_file.sync_path}:' +
            '/'.join(
                list(
                    filter(
                        lambda x: x is not None,
                        [
                            str(datetime.date.today()) if SHOULD_USE_DATETIME_CATEGORY else None,
                            getattr(leech_file, 'remote_folder'),
                            leech_file.name
                        ]
                    )
                )
            )
        )
        leech_file.upload_status = LeechFileStatus.UPLOAD_SUCCESS

        return leech_file


instance = RClone()
upload_filter = instance.upload_filter
upload = instance.upload
