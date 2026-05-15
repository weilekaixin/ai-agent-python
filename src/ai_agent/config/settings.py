from pathlib import Path

from pydantic_settings import BaseSettings

from ai_agent.models.constants import (ENV_FILE, ENV, ENV_FILE_ENCODING, ENCODING, EMPTY_STR, ROOT)
from ai_agent.models.db import (NUM_6379, NUM_19530, NUM_5432, AI_AGENT, POSTGRES, POSTGRESQL, LOCALHOST)

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
    postgres_host: str = LOCALHOST
    postgres_port: int = NUM_5432
    postgres_database: str = AI_AGENT
    postgres_username: str = POSTGRES
    postgres_password: str = EMPTY_STR
    tavily_api_key: str = EMPTY_STR

    @property
    def postgres_url(self) -> str:
        return (
            f"{POSTGRESQL}://{self.postgres_username}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    model_config = {
        ENV_FILE: BASE_DIR / ENV,
        ENV_FILE_ENCODING: ENCODING,
    }


settings = Settings()
