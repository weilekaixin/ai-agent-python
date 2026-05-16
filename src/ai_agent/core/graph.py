from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from ai_agent.config.settings import settings
from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.tool.tools import tools


# 1.定义状态
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# 2. 定义节点
def llm_node(state: AgentState):
    """LLM 节点：绑定工具的 LLM"""
    llm = get_llm().bind_tools(tools)
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState):
    """条件判断 判断大模型输出是否是需要调用工具"""
    last_message = state["messages"][-1]
    # 统计工具调用次数
    tool_call_count = sum(
        1 for msg in state["messages"]
        if hasattr(msg, "tool_calls") and msg.tool_calls
    )
    # 最多调 5 次工具
    if tool_call_count >= 5:
        return END
    # 如果大模型输出tool_calls说明需要使用工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# 3. 画图
def create_graph():
    # 创建一个状态图
    workflow = StateGraph(AgentState)  # type: ignore
    # 添加节点 大模型节点、工具节点
    workflow.add_node("llm", llm_node)  # type: ignore
    workflow.add_node("tools", ToolNode(tools))
    # 设置入口
    workflow.set_entry_point("llm")
    # 条件边：LLM 之后判断走哪条路
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "tools": "tools",  # 要调工具 → 去 tools 节点
            END: END  # 不调工具 → 结束
        }
    )
    # 设置出口
    workflow.add_edge("tools", "llm")
    # PostgreSQL checkpointer 连接时需去掉psycopg
    # 例如agent在运行到第三步系统宕机了 存入checkpointer可以恢复状态
    pg_url = settings.postgres_url.replace("postgresql+psycopg://", "postgresql://")
    pool = AsyncConnectionPool(conninfo=pg_url, max_size=20, kwargs={"autocommit": True, "row_factory": dict_row})
    checkpointer = AsyncPostgresSaver(pool)  # type: ignore
    checkpointer.setup()  # 第一次运行会自动创建表
    # 编译成可执行的图
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["tools"])
