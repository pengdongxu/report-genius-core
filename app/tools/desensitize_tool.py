import re
from app.core.tool_base import ToolBase
from app.config.settings import DESENSITIZE_CONFIG
from app.memory_store.sensitive_mapping_store import SensitiveMappingStore


class DesensitizeTool(ToolBase):
    """脱敏工具：对解析后的文本进行敏感信息脱敏"""

    name = "desensitize"

    def __init__(self):
        self._config = DESENSITIZE_CONFIG
        self._mapping_store = SensitiveMappingStore()

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        request_id = kwargs.get("request_id", "")

        rules = self._config["rules"]
        custom_rules = self._config.get("custom_rules", [])
        default_strategy = self._config["default_strategy"]

        mappings = {}
        counter = {}
        result_text = text

        # 预置规则
        for rule_name, rule_conf in rules.items():
            pattern = rule_conf.get("pattern", "")
            strategy = rule_conf.get("strategy", default_strategy)
            label = rule_conf.get("label", f"[{rule_name}]")
            result_text, new_mappings = self._apply_rule(
                result_text, pattern, strategy, label, rule_name, counter
            )
            mappings.update(new_mappings)

        # 自定义规则
        for custom_rule in custom_rules:
            pattern = custom_rule.get("pattern", "")
            strategy = custom_rule.get("strategy", default_strategy)
            label = custom_rule.get("label", "[自定义]")
            rule_name = custom_rule.get("name", "custom")
            result_text, new_mappings = self._apply_rule(
                result_text, pattern, strategy, label, rule_name, counter
            )
            mappings.update(new_mappings)

        # 持久化映射关系
        if mappings and request_id:
            self._mapping_store.save_mapping(request_id, mappings)

        return {
            "desensitized_text": result_text,
            "mapping_count": len(mappings),
        }

    @staticmethod
    def _clean_pattern(pattern: str) -> str:
        """去除正则中的 \\b 锚点，避免中文上下文边界问题。

        Python 3 中中文字符属于 \\w，导致 \\b 在中文与数字之间无法匹配。
        """
        return pattern.replace(r"\b", "")

    def _apply_rule(
        self, text: str, pattern: str, strategy: str,
        label: str, rule_name: str, counter: dict,
    ) -> tuple[str, dict]:
        """应用单条脱敏规则"""
        mappings = {}
        if not pattern:
            return text, mappings

        pattern = self._clean_pattern(pattern)
        counter[rule_name] = counter.get(rule_name, 0)

        def replacer(match):
            original = match.group(0)
            counter[rule_name] += 1
            placeholder = f"{label}_{counter[rule_name]}" if counter[rule_name] > 1 else label
            mappings[placeholder] = original

            if strategy == "placeholder":
                return placeholder
            elif strategy == "mask":
                return self._mask_value(original)
            elif strategy == "delete":
                return ""
            return placeholder

        result = re.sub(pattern, replacer, text)
        return result, mappings

    @staticmethod
    def _mask_value(value: str) -> str:
        """部分遮掩"""
        if len(value) <= 2:
            return "*" * len(value)
        return value[:3] + "****" + value[-4:]
