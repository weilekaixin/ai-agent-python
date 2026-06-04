import json
from collections import Counter
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
from ai_agent.modules.memory.auto_memory import load_auto_memory
from ai_agent.modules.skill.loader import get_skills_summary
from ai_agent.modules.tool.tools import (
    get_current_time, calculator, web_search, send_email,
    make_search_tool, get_skill_guide, deep_research, code_interpreter,
)

SENSITIVE_TOOLS = {"send_email"}


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _load_agents_md() -> str:
    path = BASE_DIR / "AGENTS.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _build_system_prompt() -> str:
    """AGENTS.md + skills registry + auto memory."""
    parts = [_load_agents_md()]
    skills = get_skills_summary()
    if skills:
        parts.append(f"\n\n{skills}")
    memory = load_auto_memory()
    if memory:
        parts.append(memory)
    return "".join(parts)


async def create_graph(retriever):
    search_tool = make_search_tool(retriever)
    safe_tools = [
        get_current_time, calculator, web_search,
        search_tool, get_skill_guide,
        deep_research, code_interpreter,  # 新增：深度研究 + 代码解释器
    ]
    sensitive_tools = [send_email]
    all_tools = safe_tools + sensitive_tools

    llm = get_llm().bind_tools(all_tools)

    def llm_node(state: AgentState):
        messages = list(state["messages"])
        if not any(isinstance(m, SystemMessage) for m in messages):
            prompt = _build_system_prompt()
            if prompt:
                messages = [SystemMessage(content=prompt)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]

        # 护栏1: 最多调用8次工具（提高上限以支持 deep_research + code 多步任务）
        tool_call_count = sum(
            1 for msg in state["messages"]
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )
        if tool_call_count >= 8:
            return END

        # 护栏2: 同一工具+参数重复3次 → 结构性终止
        signatures = [
            f"{tc['name']}:{json.dumps(tc.get('args', {}), sort_keys=True)}"
            for msg in state["messages"]
            if hasattr(msg, "tool_calls") and msg.tool_calls
            for tc in msg.tool_calls
        ]
        counts = Counter(signatures)
        if counts and counts.most_common(1)[0][1] >= 3:
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
