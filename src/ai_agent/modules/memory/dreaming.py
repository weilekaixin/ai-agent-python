"""AutoDream: nightly job that consolidates 7-day conversation history into auto_memory.md."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from ai_agent.modules.db.dao import get_sessions, get_messages_by_session
from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.memory.auto_memory import MEMORY_FILE

logger = logging.getLogger(__name__)

_DREAM_PROMPT = """\
以下是过去7天的对话摘要。
请从中提取最有价值的模式、用户偷好和未解决问题，整理成不超过30条简洁要点。
格式：每条以 "- " 开头，不超过25个汉字。
只输出要点列表，不加标题或解释。

对话内容：
{conversations}
"""


async def dream() -> str:
    """Consolidate recent sessions into auto_memory.md. Returns status string."""
    cutoff = datetime.now() - timedelta(days=7)

    sessions = get_sessions()
    recent = [s for s in sessions if s.created_time and s.created_time >= cutoff]

    if not recent:
        logger.info("dreaming: no sessions in last 7 days")
        return "no sessions"

    parts: list[str] = []
    for conv in recent:
        messages = get_messages_by_session(conv.session_id)
        if not messages:
            continue
        lines = [f"  {m.role}: {m.content[:200]}" for m in messages[:30]]
        parts.append(f"Session {conv.session_id[:8]}:\n" + "\n".join(lines))

    if not parts:
        return "no messages"

    conversation_text = "\n\n".join(parts)[:8000]  # cap token budget
    prompt = _DREAM_PROMPT.format(conversations=conversation_text)

    try:
        llm = get_llm()
        response = await llm.ainvoke(prompt)
        consolidated = response.content.strip() if hasattr(response, "content") else str(response).strip()
        if not consolidated:
            return "empty"
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d")
        # 原子性写入：直接覆盖旧文件，防止增量 append 导致内容无限膨胀
        MEMORY_FILE.write_text(
            f"# Auto Memory (last dreamed: {ts})\n\n{consolidated}\n",
            encoding="utf-8",
        )
        logger.info("dreaming: auto_memory.md updated (%d chars)", len(consolidated))
        return "ok"
    except Exception:
        logger.exception("dream() failed")
        return "error"
