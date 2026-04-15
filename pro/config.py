# ========== Конфигурация ==========
BASE_API_URL = "http://192.168.0.98:1234"
MODEL_PRIORITY = [
    {"key": "qwen/qwen3-vl-4b", "name": "QWEN"},
    {"key": "liquid/lfm2.5-1.2b", "name": "LFM"},
    {"key": "deepseek/deepseek-r1-0528-qwen3-8b", "name": "DS"},
    {"key": "meta-llama-3-8b-instruct", "name": "LLAMA"}
]
DEFAULT_CONTEXT_LENGTH = 8192
COOLDOWN_SECONDS = 10
USER_NUM = "user_1"