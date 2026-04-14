class SharedContext:
    """Agent 间共享的请求上下文"""

    def __init__(self, request_id: str):
        self.request_id = request_id
        self._data: dict = {}

    def set(self, key: str, value):
        self._data[key] = value

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def update(self, data: dict):
        self._data.update(data)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "data": self._data,
        }
