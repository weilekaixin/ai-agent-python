from datetime import datetime

from langchain_core.tools import tool
from tavily import TavilyClient

from ai_agent.config.settings import settings


@tool
def get_current_time() -> str:
    """获取实时时间"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@tool
def calculator(a: float, b: float, op: str) -> str:
    """四则运算"""
    if op == '+':
        return str(a + b)
    elif op == '-':
        return str(a - b)
    elif op == '*':
        return str(a * b)
    elif op == '/':
        return str(a / b)
    return "error"


@tool
def web_search(query: str) -> str:
    """搜索网页获取最新信息"""
    try:
        tavily = TavilyClient(api_key=settings.tavily_api_key)
        response = tavily.search(query, max_results=3)

        if not response.get("results"):
            return "未找到相关结果"

        output = []
        for i, r in enumerate(response["results"], 1):
            output.append(f"{i}，{r["title"]}\n{r["content"]}\n")
        result = "\n".join(output)
        return result
    except Exception as e:
        return f"搜索失败：{str(e)}"


# 工具列表
tools = [get_current_time, calculator, web_search]
