import json
from pathlib import Path

import requests

from nancal_langchain_base.global_conf.global_config import MASTER_SERVER, APP_UNIQUE_CODE
from nancal_langchain_base.log.node_log import logger


def initialize_agent_config():
    """
    在服务启动时请求API并将结果保存到本地文件
    """
    base_url = MASTER_SERVER+"/appApi/agents"

    # 定义配置文件路径
    agent_conf_path = Path("./config/agent_conf.json")
    model_conf_path = Path("./config/model_conf.json")

    # 检测配置文件  如果存在 则直接返回
    if agent_conf_path.exists():
        logger.info(f"Agent配置已存在,使用本地文件")
        return

    # 请求参数
    params = {"code": APP_UNIQUE_CODE}

    try:
        # 请求 agents/detail 接口
        detail_response = requests.get(
            f"{base_url}/detail",
            params=params,
            headers={"Content-Type": "application/json"}
        )

        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            with open(agent_conf_path, 'w', encoding='utf-8') as f:
                json.dump(detail_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Agent配置已保存到 {agent_conf_path}")
        else:
            logger.error(f"请求 /detail 接口失败，状态码: {detail_response.status_code}")

        # 请求 modelInfo 接口
        model_response = requests.get(
            f"{base_url}/modelInfo",
            params=params,
            headers={"Content-Type": "application/json"}
        )

        if model_response.status_code == 200:
            model_data = model_response.json()
            with open(model_conf_path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, ensure_ascii=False, indent=2)
            logger.info(f"模型配置已保存到 {model_conf_path}")
        else:
            logger.error(f"请求 /modelInfo 接口失败，状态码: {model_response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"请求异常: {e}")
    except Exception as e:
        logger.error(f"保存配置文件时发生错误: {e}")