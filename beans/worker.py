from constants.worker import WorkerStatus
from constants.mongo import WORKER_COLLECTION
from mongoengine import Document, StringField, IntField, EnumField, DateTimeField, DictField


class Worker(Document):
    hostname = StringField(required=True, primary_key=True, db_field='_id')

    queue = StringField(required=True)

    status = EnumField(WorkerStatus, required=True)

    concurrency = IntField(required=True)

    rate_limit = DictField()

    updated_at = DateTimeField()

    meta = {'collection': WORKER_COLLECTION}


