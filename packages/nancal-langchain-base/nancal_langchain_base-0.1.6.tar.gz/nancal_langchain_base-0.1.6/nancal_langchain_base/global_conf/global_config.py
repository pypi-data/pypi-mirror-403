import yaml
from pathlib import Path

def loadConfig():
    config_path = Path("config.yaml")

    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


config = loadConfig()

# 以下为config 获取的字段

# 系统配置
APP_NAME = config['application']['name']
APP_PORT = config['application']['port']
APP_TYPE = config['application']['type']
APP_MODE = config['application']['mode']
APP_LOG_LEVEL = config['application']['log_level']
MASTER_SERVER = config['application']['master_server_url']  # +   /appApi/agents/detail
APP_UNIQUE_CODE = config['application']['unique_code']  # +   /appApi/agents/modelInfo

# 模型
LLM_MODEL_NAME = config['llm']['model_name']
LLM_API_KEY = config['llm']['api_key']
LLM_BASE_URL = config['llm']['base_url']