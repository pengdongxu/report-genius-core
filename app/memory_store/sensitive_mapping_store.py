from datetime import datetime, timezone
from app.memory_store.mongo_store import MongoStore


class SensitiveMappingStore:
    """脱敏映射关系持久化"""

    COLLECTION = "sensitive_mappings"

    def __init__(self):
        self._store = MongoStore()
        self._collection = self._store.db[self.COLLECTION]

    def save_mapping(self, request_id: str, mappings: dict):
        self._collection.insert_one({
            "request_id": request_id,
            "created_at": datetime.now(timezone.utc),
            "mappings": mappings,
        })

    def get_mapping(self, request_id: str) -> dict | None:
        doc = self._collection.find_one({"request_id": request_id})
        if doc:
            return doc.get("mappings")
        return None
