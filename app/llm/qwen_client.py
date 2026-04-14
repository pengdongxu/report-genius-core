from dashscope import Generation
from app.config.settings import LLM_CONFIG


class QwenClient:
    """通义千问 API 客户端"""

    def chat(self, model: str, message: str, system_prompt: str = "") -> str:
        return self._call_api(model, message, system_prompt)

    def _call_api(self, model: str, message: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = Generation.call(
            model=model,
            messages=messages,
            api_key=LLM_CONFIG["api_key"],
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        raise RuntimeError(f"LLM call failed: {response.status_code} - {response.message}")
