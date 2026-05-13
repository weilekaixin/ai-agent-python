# 全局常量 — 配置、业务常量统一管理

# 配置文件
ENV = ".env"
ENCODING = "utf-8"
ENV_FILE = "env_file"
ENV_FILE_ENCODING = "env_file_encoding"

# 模型默认值
DEEPSEEK_MODEL = "openai:deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# 角色
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"
TOOL_ROLE = "tool"

# 字符串常量
EMPTY_STR = ""
# 数字常量
TEN_NUM = 10

# 业务字段
NAME = "name"
ARGS = "args"
ID = "id"
TOOL_CALL_ID = "tool_call_id"

# 系统提示词
RAG_SYSTEM_PROMPT = "基于以下资料回答问题。如果资料中没有相关信息，你可以根据自己的知识回答："
QUESTION = "\n问题："