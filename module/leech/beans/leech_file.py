import uuid
import datetime
from constants.mongo import FILE_COLLECTION
from module.leech.constants.leech_file_status import LeechFileStatus
from mongoengine import Document, StringField, IntField, EnumField, DateTimeField
from module.leech.constants.leech_file_tool import LeechFileTool, LeechFileSyncTool


class LeechFile(Document):
    # uuid of the file
    id = StringField(default=lambda: str(uuid.uuid4()), primary_key=True, db_field='_id')
    # link of the file
    link = StringField(required=True)
    # tool used to download the file
    tool = EnumField(LeechFileTool, required=True)
    # file download status
    status = EnumField(LeechFileStatus, default=LeechFileStatus.INITIAL)
    # file upload status
    upload_status = EnumField(LeechFileStatus, default=LeechFileStatus.INITIAL)
    # sync tool used to upload the file
    sync_tool = EnumField(LeechFileSyncTool, default=None)
    # file name
    name = StringField()
    # reason for the file status if error occurs
    reason = StringField()
    upload_reason = StringField()
    # remote folder to store the file
    remote_folder = StringField()
    # location of the file
    location = StringField()
    # path to sync the file
    sync_path = StringField()
    # size of the file
    size = IntField()
    # hash of the file
    file_hash = StringField()
    #
    created_at = DateTimeField(default=lambda: datetime.datetime.utcnow())
    #
    updated_at = DateTimeField()

    meta = {'allow_inheritance': True, 'collection': FILE_COLLECTION}

    def get_full_name(self):
        return f'{self.location}/tmp'

    def get_temp_full_name(self):
        return f'{self.get_full_name()}.part'
