import json
from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from ai_agent.config.settings import settings, BASE_DIR
from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.tool.tools import get_current_time, calculator, web_search, send_email, make_search_tool

SENSITIVE_TOOLS = {"send_email"}


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _load_agents_md() -> str:
    """加载 AGENTS.md 作为系统提示词基础"""
    path = BASE_DIR / "AGENTS.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


async def create_graph(retriever):
    """创建 LangGraph 图，retriever 由外部注入"""
    search_tool = make_search_tool(retriever)
    safe_tools = [get_current_time, calculator, web_search, search_tool]
    sensitive_tools = [send_email]
    all_tools = safe_tools + sensitive_tools

    # LLM 绑定工具，单例创建，避免每次节点调用都 new 实例
    llm = get_llm().bind_tools(all_tools)
    # 系统提示词在启动时加载一次，运行期不变
    system_prompt = _load_agents_md()

    def llm_node(state: AgentState):
        messages = list(state["messages"])
        # 首轮对话注入系统提示词，后续轮次已有 SystemMessage 则跳过
        if system_prompt and not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        tool_call_count = sum(
            1 for msg in state["messages"]
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )
        if tool_call_count >= 5:
            return END
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_names = {tc["name"] for tc in last_message.tool_calls}
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
        {"safe_tools": "safe_tools", "sensitive_tools": "sensitive_tools", END: END},
    )
    workflow.add_edge("safe_tools", "llm")
    workflow.add_edge("sensitive_tools", "llm")

    pg_url = settings.postgres_url.replace("postgresql+psycopg://", "postgresql://")
    pool = AsyncConnectionPool(
        conninfo=pg_url,
        max_size=20,
        kwargs={"autocommit": True, "row_factory": dict_row},
        open=False,
    )
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)  # type: ignore
    await checkpointer.setup()

    return workflow.compile(checkpointer=checkpointer, interrupt_before=["sensitive_tools"])
