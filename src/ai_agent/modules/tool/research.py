"""Deep Research — decompose → parallel search → synthesize → cite."""
from __future__ import annotations

import asyncio
import logging
from functools import partial

from langchain_core.tools import tool

from ai_agent.config.settings import settings
from ai_agent.utils.scraper import scrape_search

logger = logging.getLogger(__name__)

_DECOMPOSE_PROMPT = """\
将以下研究问题分解为 3-5 个独立的搜索子查询，每行一个，不加序号。
确保子查询覆盖问题的不同维度。只输出查询词，不加任何解释。
问题：{query}
"""

_SYNTHESIZE_PROMPT = """\
你是一位专业研究分析师。基于以下多源搜索结果，对问题「{query}」给出综合分析报告。
要求：
1. 综合所有来源的关键信息
2. 用 [来源: URL] 标注重要事实
3. 指出信息不确定或来源冲突之处
4. 末尾给出清晰结论

搜索结果：
{results}
"""


@tool
async def deep_research(query: str) -> str:
    """对复杂问题进行深度多步研究：自动分解问题→并行搜索→综合分析→注明来源。
    适合需要全面调研的场景：市场分析、技术对比、事件背景调查、竞品研究等。

    Args:
        query: 需要深度研究的问题或主题
    """
    if not settings.search_url:
        return "深度研究需要配置 SEARCH_URL 环境变量"

    from ai_agent.modules.llm.factory import get_llm
    llm = get_llm()

    # Step 1: 分解为子查询
    try:
        plan = await llm.ainvoke(_DECOMPOSE_PROMPT.format(query=query))
        sub_queries = [line.strip() for line in plan.content.strip().splitlines() if line.strip()][:5]
    except Exception:
        sub_queries = [query]

    if not sub_queries:
        sub_queries = [query]

    logger.info("deep_research: %d sub-queries for %r", len(sub_queries), query[:60])

    # Step 2: 并行搜索（scrape_search 是同步函数，用 run_in_executor 转异步）
    loop = asyncio.get_event_loop()

    async def _search(q: str) -> tuple[str, str]:
        try:
            result = await loop.run_in_executor(
                None, partial(scrape_search, settings.search_url, q)
            )
            return q, result
        except Exception as e:
            return q, f"搜索失败: {e}"

    pairs = await asyncio.gather(*[_search(q) for q in sub_queries])

    # Step 3: 综合分析
    results_text = "\n\n".join(
        f"子问题「{q}」:\n{r[:2000]}"
        for q, r in pairs if r
    )
    if not results_text:
        return "未能获取搜索结果，请检查 SEARCH_URL 配置"

    try:
        synth = await llm.ainvoke(
            _SYNTHESIZE_PROMPT.format(query=query, results=results_text[:8000])
        )
        return synth.content
    except Exception as e:
        return f"综合分析失败: {e}\n\n原始搜索摘要:\n{results_text[:2000]}"
