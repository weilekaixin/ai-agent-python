"""Auto Memory: extract key learnings after each conversation and persist them."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

from ai_agent.config.settings import BASE_DIR
from ai_agent.modules.llm.factory import get_llm

logger = logging.getLogger(__name__)

MEMORY_FILE = BASE_DIR / "memory" / "auto_memory.md"

_CONSOLIDATE_PROMPT = """\
以下是一次与用户的对话记录。
请提取 2-3 条对未来对话有价值的要点，也可以是用户的偶发奔头、特殊偏好或当前未解决问题。
格式：每条以 "- " 开头，不超过 20 个汉字。
只输出子弹内容，不要加标题或解释。

对话记录：
{conversation}
"""


def load_auto_memory() -> str:
    if not MEMORY_FILE.exists():
        return ""
    content = MEMORY_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return ""
    return f"\n\n## Auto Memory (cross-session learnings)\n{content}"


def _append_memory(note: str) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n### {ts}\n{note}\n")


async def consolidate_conversation(messages: list[BaseMessage]) -> None:
    """Extract learnings from a completed conversation and append to auto_memory.md."""
    from langchain_core.messages import HumanMessage, AIMessage
    turns = [
        m for m in messages
        if isinstance(m, (HumanMessage, AIMessage)) and isinstance(m.content, str) and m.content.strip()
    ]
    if len(turns) < 2:
        return

    conversation_text = "\n".join(
        f"{('User' if isinstance(m, HumanMessage) else 'AI')}: {m.content[:300]}"
        for m in turns[-20:]  # 最近20条避免 token 过多
    )
    prompt = _CONSOLIDATE_PROMPT.format(conversation=conversation_text)
    try:
        llm = get_llm()
        response = await llm.ainvoke(prompt)
        note = response.content.strip() if hasattr(response, "content") else str(response).strip()
        if note:
            _append_memory(note)
    except Exception:
        logger.exception("consolidate_conversation failed, skipping")
