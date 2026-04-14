class Registry:
    """Tool 和 Agent 的注册表"""

    def __init__(self):
        self._items: dict[str, object] = {}

    def register(self, name: str, item):
        self._items[name] = item

    def get(self, name: str):
        if name not in self._items:
            raise KeyError(f"'{name}' not registered")
        return self._items[name]

    def list_all(self) -> list[str]:
        return list(self._items.keys())
