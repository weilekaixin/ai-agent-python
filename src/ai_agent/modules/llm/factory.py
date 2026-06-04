from functools import lru_cache

from langchain.chat_models import init_chat_model

from ai_agent.config.settings import settings
from ai_agent.models.constants import DEEPSEEK_MODEL, DEEPSEEK_BASE_URL


@lru_cache(maxsize=1)
def get_llm():
    """初始化大模型（单例，运行期只创建一次连接）"""
    return init_chat_model(
        DEEPSEEK_MODEL,
        api_key=settings.deepseek_api_key,
        base_url=DEEPSEEK_BASE_URL,
    )
