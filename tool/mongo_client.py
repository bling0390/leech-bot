from mongoengine import connect
from beans.singleton import Singleton
from config.config import MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE_NAME


class EstablishConnection(Singleton):
    def __init__(self):
        connect(
            db=MONGO_DATABASE_NAME,
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD,
            host=f'mongodb://{MONGO_HOST}:{MONGO_PORT}/'
        )
