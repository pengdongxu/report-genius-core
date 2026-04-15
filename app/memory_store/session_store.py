from datetime import datetime, timezone
from app.memory_store.mongo_store import MongoStore


class SessionStore:
    """基于 MongoDB 的会话存储"""

    def __init__(self):
        self._collection = MongoStore().db["sessions"]

    def get_or_create_session(self, session_id: str) -> dict:
        session = self._collection.find_one({"session_id": session_id})
        if session:
            return session
        now = datetime.now(timezone.utc)
        session = {
            "session_id": session_id,
            "messages": [],
            "context": {},
            "created_at": now,
            "updated_at": now,
        }
        self._collection.insert_one(session)
        return session

    def save_message(self, session_id: str, role: str, content: str):
        now = datetime.now(timezone.utc)
        self._collection.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "role": role,
                        "content": content,
                        "timestamp": now,
                    }
                },
                "$set": {"updated_at": now},
            },
        )

    def get_messages(self, session_id: str) -> list[dict]:
        session = self._collection.find_one({"session_id": session_id})
        return session["messages"] if session else []

    def save_context(self, session_id: str, context: dict):
        now = datetime.now(timezone.utc)
        self._collection.update_one(
            {"session_id": session_id},
            {"$set": {"context": context, "updated_at": now}},
        )

    def get_context(self, session_id: str) -> dict:
        session = self._collection.find_one({"session_id": session_id})
        return session.get("context", {}) if session else {}
