from langchain_community.cache import RedisCache
from langchain_core.globals import set_llm_cache
from langchain_core.messages import HumanMessage, AIMessage

from ai_agent.config.settings import settings
from ai_agent.modules.cache.client import get_redis_client
from ai_agent.modules.cache.history import get_history
from ai_agent.modules.rag.retriever import get_retriever
from ai_agent.modules.rag.store import build_vector_store


def setup_llm_cache():
    """开启 Redis LLM 响应缓存"""
    set_llm_cache(RedisCache(redis_=get_redis_client()))


def create_rag_retriever(file_path: str):
    """建向量库，返回检索器"""
    store = build_vector_store(file_path)
    return get_retriever(store)


def build_messages_with_history(session_id: str, user_message: str) -> list:
    """取 Redis 历史消息，拼接当前用户消息，返回完整消息列表。

    保留最近 history_max_pairs 轮对话，避免超出模型上下文窗口。
    """
    history = get_history(session_id)
    messages = []
    for msg in history:
        if msg["role"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))

    # Truncate to most recent N pairs (2 messages per pair)
    max_msgs = settings.history_max_pairs * 2
    if len(messages) > max_msgs:
        messages = messages[-max_msgs:]

    messages.append(HumanMessage(content=user_message))
    return messages
