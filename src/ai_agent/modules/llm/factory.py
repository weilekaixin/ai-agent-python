from langchain.chat_models import init_chat_model

from ai_agent.config.settings import settings
from ai_agent.models.constants import DEEPSEEK_MODEL, DEEPSEEK_BASE_URL


def get_llm():
    """初始化大模型"""
    return init_chat_model(DEEPSEEK_MODEL, api_key=settings.deepseek_api_key, base_url=DEEPSEEK_BASE_URL)
