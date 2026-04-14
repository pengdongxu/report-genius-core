from pymongo import MongoClient
from app.config.settings import MONGO_CONFIG


class MongoStore:
    """MongoDB 持久化操作"""

    def __init__(self):
        self._client = MongoClient(MONGO_CONFIG["uri"])
        self._db = self._client[MONGO_CONFIG["db_name"]]

    @property
    def db(self):
        return self._db
