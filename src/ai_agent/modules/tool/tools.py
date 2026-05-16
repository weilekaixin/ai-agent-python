from datetime import datetime

from langchain_core.tools import tool

from ai_agent.config.settings import settings
from ai_agent.utils.email_sender import send_email as _send_email
from ai_agent.utils.scraper import scrape_search


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
        return scrape_search(settings.search_url, query)
    except Exception as e:
        return f"搜索失败：{str(e)}"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件。这是一个敏感操作，会真实发送邮件。

    Args:
        to: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
    """
    try:
        return _send_email(to, subject, body)
    except Exception as e:
        return f"邮件发送失败：{str(e)}"


# 工具列表
tools = [get_current_time, calculator, web_search, send_email]
