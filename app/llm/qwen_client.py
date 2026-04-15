from dashscope import Generation
from app.config.settings import LLM_CONFIG


class QwenClient:
    """通义千问 API 客户端"""

    def chat(self, model: str, message: str, system_prompt: str = "", history: list[dict] | None = None) -> str:
        return self._call_api(model, message, system_prompt, history)

    def _call_api(self, model: str, message: str, system_prompt: str = "", history: list[dict] | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        response = Generation.call(
            model=model,
            messages=messages,
            api_key=LLM_CONFIG["api_key"],
            result_format="message",
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"LLM call failed: status={response.status_code}, "
                f"message={response.message}"
            )

        if not response.output or not response.output.choices:
            raise RuntimeError(
                f"LLM returned empty output: request_id={response.request_id}, "
                f"output={response.output}"
            )

        return response.output.choices[0].message.content
