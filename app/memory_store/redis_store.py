import redis
from app.config.settings import REDIS_CONFIG


class RedisStore:
    """Redis 缓存操作"""

    def __init__(self):
        self._client = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            db=REDIS_CONFIG["db"],
            password=REDIS_CONFIG["password"] or None,
            decode_responses=True,
        )

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, expire: int = 3600):
        self._client.set(key, value, ex=expire)

    def delete(self, key: str):
        self._client.delete(key)
