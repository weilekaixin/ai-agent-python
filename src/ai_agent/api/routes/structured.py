from typing import Any

from fastapi import APIRouter
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ai_agent.api.schemas.common import fail, ok
from ai_agent.modules.llm.factory import get_llm

router = APIRouter()

_DEFAULT_SYS = "你是一个结构化信息提取助手，请严格按照指定格式提取信息。"


class StructuredRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    # 接收任意 JSON Schema，也可是 Pydantic 能识别的结构
    schema_def: dict[str, Any] = Field(
        ...,
        alias="schema",
        description="JSON Schema 定义期望的输出格式",
    )
    system_prompt: str = Field(default=_DEFAULT_SYS, max_length=2000)

    model_config = {"populate_by_name": True}


@router.post("/structured", tags=["ai"])
async def structured_output(body: StructuredRequest):
    """结构化输出接口：按照 JSON Schema 提取 / 生成结构化数据。

    适用场景：
    - 信息提取（姓名、日期、金额等字段提取）
    - 意图分类与实体识别
    - 表单自动填写
    - 文本标注与分类
    - 业务数据解析

    示例 schema:
    ```json
    {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "amount": {"type": "number"},
        "category": {"type": "string", "enum": ["food", "transport", "other"]}
      }
    }
    ```
    """
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(body.schema_def)
        result = await structured_llm.ainvoke([
            SystemMessage(content=body.system_prompt),
            HumanMessage(content=body.message),
        ])
        return ok(result)
    except Exception as e:
        return fail(500, f"结构化提取失败: {e}")
