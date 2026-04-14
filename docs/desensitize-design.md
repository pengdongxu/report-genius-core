# 脱敏设计（Desensitize）

## 一、定位

独立 Tool，插拔式，由 Orchestrator 在 Parser 之后、Extract 之前调度。

```
Parser（解析） → Desensitize（脱敏） → Extract（结构化） → ...
```

## 二、脱敏规则

### 预置规则

| 规则类型 | 说明 |
| --- | --- |
| name | 姓名 |
| id_card | 身份证号 |
| phone | 手机号 |
| address | 地址 |
| medical_id | 就诊号/门诊号 |
| record_no | 病历号 |
| bed_no | 床号/床位 |
| hospital_name | 医院/卫生院/诊所/中心 |

### 自定义规则

支持通过 `settings.py` 的 `custom_rules` 配置额外的正则/关键词规则。

## 三、替换策略（可配置）

| 策略 | 示例 | 说明 |
| --- | --- | --- |
| placeholder | 张三 → [姓名] | 默认策略，下游 Tool 可理解数据结构 |
| mask | 13812345678 → 138****5678 | 保留部分可读性 |
| delete | 直接移除敏感字段 | 完全去除 |

每种规则类型可在 `settings.py` 中独立配置策略。

## 四、映射关系持久化

映射关系写入 MongoDB（`sensitive_mappings` 集合），用于审计追溯：

```json
{
  "request_id": "req_xxx",
  "created_at": "2026-04-14T22:00:00",
  "mappings": {
    "[姓名_1]": "张三",
    "[手机号_1]": "13812345678"
  }
}
```

## 五、配置结构

所有脱敏规则在 `app/config/settings.py` 的 `DESENSITIZE_CONFIG` 中配置：

```python
DESENSITIZE_CONFIG = {
    "rules": {
        "name":          {"pattern": r"...", "strategy": "placeholder", "label": "[姓名]"},
        "id_card":       {"pattern": r"...", "strategy": "placeholder", "label": "[身份证号]"},
        "phone":         {"pattern": r"...", "strategy": "mask",        "label": ""},
        "address":       {"pattern": r"...", "strategy": "placeholder", "label": "[地址]"},
        "medical_id":    {"pattern": r"...", "strategy": "placeholder", "label": "[就诊号]"},
        "record_no":     {"pattern": r"...", "strategy": "placeholder", "label": "[病历号]"},
        "bed_no":        {"pattern": r"...", "strategy": "placeholder", "label": "[床号]"},
        "hospital_name": {"pattern": r"...", "strategy": "placeholder", "label": "[医院名称]"},
    },
    "custom_rules": [],
    "default_strategy": "placeholder",
}
```
