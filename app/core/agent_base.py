from abc import ABC, abstractmethod


class AgentBase(ABC):
    """Agent 基类"""
    name: str = ""

    @abstractmethod
    def run(self, context: dict) -> dict:
        """执行 Agent 逻辑，context 为共享上下文"""
        ...
