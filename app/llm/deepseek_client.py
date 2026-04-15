from openai import OpenAI
from app.config.settings import LLM_CONFIG


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self):
        config = LLM_CONFIG["deepseek"]
        self._client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
        )

    def chat(self, model: str, message: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
        )

        if response.choices:
            return response.choices[0].message.content
        raise RuntimeError(f"DeepSeek call failed: no choices returned")
