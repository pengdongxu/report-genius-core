import os


# LLM 配置
LLM_CONFIG = {
    "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
    "models": {
        "parser": "qwen-vl-max",
        "extract": "qwen-plus",
        "explain": "qwen-max",
        "planner": "qwen-plus",
    },
    "embedding": {
        "model": "text-embedding-v2",
        "dimension": 1536,
    },
}

# RAG 配置
RAG_CONFIG = {
    "faiss_index_path": os.getenv("FAISS_INDEX_PATH", "./data/faiss_index"),
    "top_k": 5,
    "score_threshold": 0.7,
}

# Redis 配置
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD", ""),
}

# MongoDB 配置
MONGO_CONFIG = {
    "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    "db_name": os.getenv("MONGO_DB_NAME", "report_genius"),
}

# 脱敏配置
DESENSITIZE_CONFIG = {
    "rules": {
        "name":          {"pattern": r"[\u4e00-\u9fa5]{2,4}(?=的|先生|女士|患者)", "strategy": "placeholder", "label": "[姓名]"},
        "id_card":       {"pattern": r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b", "strategy": "placeholder", "label": "[身份证号]"},
        "phone":         {"pattern": r"\b1[3-9]\d{9}\b", "strategy": "mask", "label": ""},
        "address":       {"pattern": r"[\u4e00-\u9fa5]{2,}(?:省|市|区|县|镇|乡|村|路|号|栋|室)", "strategy": "placeholder", "label": "[地址]"},
        "medical_id":    {"pattern": r"(?:就诊号|门诊号)[：:]\s*\S+", "strategy": "placeholder", "label": "[就诊号]"},
        "record_no":     {"pattern": r"(?:病历号)[：:]\s*\S+", "strategy": "placeholder", "label": "[病历号]"},
        "bed_no":        {"pattern": r"(?:床号|床位)[：:]\s*\S+", "strategy": "placeholder", "label": "[床号]"},
        "hospital_name": {"pattern": r"[\u4e00-\u9fa5]{2,}(?:医院|卫生院|诊所|中心)", "strategy": "placeholder", "label": "[医院名称]"},
    },
    "custom_rules": [],
    "default_strategy": "placeholder",
}

# Web Search 配置
WEB_SEARCH_CONFIG = {
    "enabled": False,
    "rag_confidence_threshold": 0.5,
}
