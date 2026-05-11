from pydantic_settings import BaseSettings
from ai_agent.models.constants import ENCODING, ENV, ENV_FILE, ENV_FILE_ENCODING, EMPTY_STR


class Settings(BaseSettings):
    deepseek_api_key: str = EMPTY_STR

    model_config = {
        ENV_FILE: ENV,
        ENV_FILE_ENCODING: ENCODING,
    }


settings = Settings()
