import datetime

from constants.mongo import SETTING_COLLECTION
from mongoengine import Document, DateTimeField, DictField, EnumField

from constants.setting import SettingKey


class Setting(Document):
    key = EnumField(SettingKey, required=True, primary_key=True, db_field='_id')

    value = DictField(required=True)

    created_at = DateTimeField(default=lambda: datetime.datetime.utcnow())

    updated_at = DateTimeField()

    meta = {'collection': SETTING_COLLECTION}


