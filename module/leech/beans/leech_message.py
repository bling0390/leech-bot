import uuid
import datetime
from constants.mongo import MESSAGE_COLLECTION
from module.leech.constants.leech_file_status import LeechFileStatus
from module.leech.constants.message import MessageStatus
from module.leech.constants.task import TaskType, TaskStatus
from mongoengine import Document, StringField, EnumField, DateTimeField


class LeechMessage(Document):
    id = StringField(default=lambda: str(uuid.uuid4()), primary_key=True, db_field='_id')

    phase = EnumField(TaskType, required=True)

    file_id = StringField(required=True)

    receiver = StringField()

    content = StringField(required=True)

    status = EnumField(MessageStatus, required=True)

    file_status = EnumField(LeechFileStatus, required=True)
    #
    created_at = DateTimeField(default=lambda: datetime.datetime.utcnow())
    #
    updated_at = DateTimeField()

    meta = {'collection': MESSAGE_COLLECTION}
