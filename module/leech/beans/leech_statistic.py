from constants.mongo import STATISTIC_COLLECTION
from module.leech.constants.statistic import StatisticItem
from mongoengine import Document, StringField, DateTimeField, EnumField


class LeechStatistic(Document):
    name = EnumField(StatisticItem, required=True, primary_key=True, db_field='_id')

    value = StringField(required=True)

    updated_at = DateTimeField()

    meta = {'collection': STATISTIC_COLLECTION}
