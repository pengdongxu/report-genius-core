from abc import ABC, abstractmethod


class ToolBase(ABC):
    """能力模块基类"""
    name: str = ""

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """执行工具，返回结果字典"""
        ...
