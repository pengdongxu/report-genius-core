from app.core.agent_base import AgentBase


class MemoryAgent(AgentBase):
    """上下文管理 Agent：管理请求生命周期内的共享数据"""

    name = "memory"

    def run(self, context) -> dict:
        return context.to_dict()
