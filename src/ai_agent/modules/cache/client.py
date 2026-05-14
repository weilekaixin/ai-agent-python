import redis
from ai_agent.config.settings import settings


def get_redis_client() -> redis.Redis:
    """获取 Redis 连接"""
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password or None,
        decode_responses=True,
    )