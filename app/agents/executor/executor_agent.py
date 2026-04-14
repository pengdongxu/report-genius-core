from app.core.agent_base import AgentBase
from app.core.registry import Registry


class ExecutorAgent(AgentBase):
    """执行器 Agent：按计划执行 Tool 链路"""

    name = "executor"

    def __init__(self):
        self._registry = Registry()

    def register_tool(self, name_or_tool, tool=None):
        """注册 Tool。支持两种调用方式：
        - register_tool(tool_instance)  单参数，通过 tool.name 注册
        - register_tool(name, tool_instance)  双参数，显式指定名称
        """
        if tool is not None:
            self._registry.register(name_or_tool, tool)
        else:
            self._registry.register(name_or_tool.name, name_or_tool)

    def run(self, params: dict) -> dict:
        context = params["context"]
        plan = params["plan"]

        for step in plan:
            tool_name = step["tool"]
            tool_params = step.get("params", {})

            tool = self._registry.get(tool_name)

            # 从 context 中提取上游数据注入参数
            if tool_name == "desensitize":
                tool_params["text"] = context.get("parser_result", {}).get("text", "")
                tool_params["request_id"] = context.request_id
            elif tool_name == "extract":
                tool_params["text"] = context.get("desensitize_result", {}).get("desensitized_text", "")
            elif tool_name == "rag":
                extracted = context.get("extract_result", {}).get("extracted_data", [])
                tool_params["query"] = " ".join(
                    [item.get("name", "") for item in extracted if item.get("is_abnormal")]
                ) if extracted else ""
            elif tool_name == "explain":
                tool_params["extracted_data"] = context.get("extract_result", {}).get("extracted_data", [])
                tool_params["references"] = context.get("rag_result", {}).get("formatted_context", "")

            result = tool.execute(**tool_params)
            context.set(f"{tool_name}_result", result)

        return context.to_dict()
