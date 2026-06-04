from __future__ import annotations

from collections import Counter
from functools import lru_cache
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.tool.code_exec import code_interpreter
from ai_agent.modules.tool.research import deep_research
from ai_agent.modules.tool.tools import web_search, calculator, get_current_time

_ROUTER_PROMPT = """\
你是智能任务路由器。根据用户最新消息决定路由到哪个专业智能体：
- researcher: 需要深度研究、联网搜索、信息汇总
- coder: 需要编写、运行或调试代码、数学推导
- general: 普通对话、问答、写作等其他任务
只输出一个单词: researcher, coder, 或 general。不含其他内容。"""

_WORKER_PROMPTS = {
    "researcher": "你是研究专家，擅长深度研究和信息综合。优先使用 deep_research 工具获取全面信息。",
    "coder": "你是代码专家，擅长编写和调试代码。使用 code_interpreter 执行代码并返回结果。",
    "general": "你是智能助手，专注回答用户问题，提供清晰准确的信息。",
}

_WORKER_TOOLS: dict[str, list] = {
    "researcher": [deep_research, web_search],
    "coder": [code_interpreter, calculator],
    "general": [get_current_time, calculator, web_search],
}

# Deduplicated union of all worker tools (by tool name)
_all_tools = list({t.name: t for tools in _WORKER_TOOLS.values() for t in tools}.values())


class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    worker: str


async def _supervisor(state: SupervisorState) -> dict:
    llm = get_llm()
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        state["messages"][-1].content if state["messages"] else "",
    )
    response = await llm.ainvoke([
        SystemMessage(content=_ROUTER_PROMPT),
        HumanMessage(content=str(last_human)),
    ])
    raw = response.content.strip().lower().split()[0] if response.content.strip() else "general"
    worker = raw if raw in _WORKER_TOOLS else "general"
    return {"worker": worker}


def _worker(state: SupervisorState) -> dict:
    worker = state.get("worker", "general")  # type: ignore[call-overload]
    tools = _WORKER_TOOLS.get(worker, _WORKER_TOOLS["general"])
    llm = get_llm().bind_tools(tools)
    sys_msg = SystemMessage(content=_WORKER_PROMPTS.get(worker, _WORKER_PROMPTS["general"]))
    msgs = list(state["messages"])
    if not any(isinstance(m, SystemMessage) for m in msgs):
        msgs = [sys_msg] + msgs
    return {"messages": [llm.invoke(msgs)]}


def _should_continue(state: SupervisorState) -> str:
    last = state["messages"][-1]
    if not (hasattr(last, "tool_calls") and last.tool_calls):
        return END
    tool_call_count = sum(
        1 for m in state["messages"]
        if hasattr(m, "tool_calls") and m.tool_calls
    )
    if tool_call_count >= 5:
        return END
    signatures = [
        f"{tc['name']}:{tc.get('args', {})}"
        for m in state["messages"]
        if hasattr(m, "tool_calls") and m.tool_calls
        for tc in m.tool_calls
    ]
    if signatures and Counter(signatures).most_common(1)[0][1] >= 3:
        return END
    return "tools"


@lru_cache(maxsize=1)
def get_supervisor_graph():
    """Supervisor multi-agent graph (singleton, no checkpointer)."""
    g = StateGraph(SupervisorState)
    g.add_node("supervisor", _supervisor)
    g.add_node("worker", _worker)
    g.add_node("tools", ToolNode(_all_tools))

    g.set_entry_point("supervisor")
    g.add_edge("supervisor", "worker")
    g.add_conditional_edges("worker", _should_continue, {"tools": "tools", END: END})
    g.add_edge("tools", "worker")

    return g.compile()
