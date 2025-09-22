import uuid
import datetime
from constants.mongo import TASK_COLLECTION
from module.leech.constants.task import TaskType, TaskStatus
from mongoengine import Document, StringField, EnumField, DateTimeField


class LeechTask(Document):
    id = StringField(default=lambda: str(uuid.uuid4()), primary_key=True, db_field='_id')

    task_id = StringField(required=True)

    file_id = StringField(required=True)

    type = EnumField(TaskType, required=True)

    status = EnumField(TaskStatus, required=True)
    #
    created_at = DateTimeField(default=lambda: datetime.datetime.utcnow())
    #
    updated_at = DateTimeField()

    meta = {'collection': TASK_COLLECTION}
