from app.core.agent_base import AgentBase


class PlannerAgent(AgentBase):
    """任务规划 Agent：生成 Tool 执行计划"""

    name = "planner"

    def run(self, context) -> list[dict]:
        # Phase 1: 返回固定流程计划
        return [
            {"tool": "parser", "params": {"input_type": context.get("input_type", "text")}},
            {"tool": "desensitize", "params": {}},
            {"tool": "extract", "params": {}},
            {"tool": "rag", "params": {}},
            {"tool": "explain", "params": {}},
        ]
