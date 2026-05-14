from pathlib import Path

from pydantic_settings import BaseSettings

from ai_agent.models.constants import (ENV_FILE, ENV, ENV_FILE_ENCODING, ENCODING, EMPTY_STR, LOCALHOST, NUM_6379,
                                       NUM_19530, ROOT)

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    deepseek_api_key: str = EMPTY_STR
    redis_host: str = LOCALHOST
    redis_port: int = NUM_6379
    redis_password: str = EMPTY_STR
    milvus_host: str = LOCALHOST
    milvus_port: int = NUM_19530
    milvus_user: str = ROOT
    milvus_password: str = EMPTY_STR
    model_config = {
        ENV_FILE: BASE_DIR / ENV,
        ENV_FILE_ENCODING: ENCODING,
    }


settings = Settings()
