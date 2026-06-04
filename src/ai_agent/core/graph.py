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
from ai_agent.modules.tool.tools import get_current_time, calculator, web_search, send_email, make_search_tool

# 需要人工确认的敏感工具名称集合
SENSITIVE_TOOLS = {"send_email"}


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


async def create_graph(retriever):
    """创建 LangGraph 图，retriever 由外部注入"""
    # 构建工具列表
    search_tool = make_search_tool(retriever)
    safe_tools = [get_current_time, calculator, web_search, search_tool]
    sensitive_tools = [send_email]
    all_tools = safe_tools + sensitive_tools

    # LLM 绑定工具，单例创建，避免每次节点调用都 new 一个实例
    llm = get_llm().bind_tools(all_tools)

    def llm_node(state: AgentState):
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        # 防止死循环：最多调用工具 5 次
        tool_call_count = sum(
            1 for msg in state["messages"]
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )
        if tool_call_count >= 5:
            return END
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_names = {tc["name"] for tc in last_message.tool_calls}
            # 有敏感工具就走 sensitive_tools 节点（会被 interrupt_before 拦截）
            if tool_names & SENSITIVE_TOOLS:
                return "sensitive_tools"
            return "safe_tools"
        return END

    workflow = StateGraph(AgentState)  # type: ignore
    workflow.add_node("llm", llm_node)  # type: ignore
    workflow.add_node("safe_tools", ToolNode(safe_tools))
    workflow.add_node("sensitive_tools", ToolNode(sensitive_tools))
    workflow.set_entry_point("llm")
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "safe_tools": "safe_tools",
            "sensitive_tools": "sensitive_tools",
            END: END,
        }
    )
    workflow.add_edge("safe_tools", "llm")
    workflow.add_edge("sensitive_tools", "llm")

    # 异步创建连接池，必须在 async 上下文中 open
    pg_url = settings.postgres_url.replace("postgresql+psycopg://", "postgresql://")
    pool = AsyncConnectionPool(
        conninfo=pg_url,
        max_size=20,
        kwargs={"autocommit": True, "row_factory": dict_row},
        open=False,
    )
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)  # type: ignore
    await checkpointer.setup()  # 第一次运行自动建表，必须 await

    # 只对敏感工具节点触发人工审批中断
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["sensitive_tools"])
