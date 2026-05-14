import json
from ai_agent.models.cache import MESSAGE_HISTORY, MESSAGE_HISTORY_TIME
from ai_agent.modules.cache.client import get_redis_client

redis_client = get_redis_client()
MAX_HISTORY = 20  # 最多保留20条消息


def get_history(session_id: str) -> list:
    """从 Redis List 取最近20条对话历史"""
    key = f"{MESSAGE_HISTORY}{session_id}"
    items = redis_client.lrange(key, -MAX_HISTORY, -1)  # type: ignore
    return [json.loads(item) for item in items]


def save_message(session_id: str, role: str, content: str) -> None:
    """追加单条消息到 Redis List"""
    key = f"{MESSAGE_HISTORY}{session_id}"
    redis_client.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))  # type: ignore
    redis_client.expire(key, MESSAGE_HISTORY_TIME)


def clear_history(session_id: str) -> None:
    """清除对话历史"""
    redis_client.delete(f"{MESSAGE_HISTORY}{session_id}")  # type: ignore
