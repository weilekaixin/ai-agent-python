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
        if b == 0:
            return "除数不能为零"
        return str(a / b)
    return "不支持的运算符"


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


def make_search_tool(retriever):
    """用闭包注入 retriever，创建知识库检索工具"""
    @tool
    def search_knowledge_base(query: str) -> str:
        """当用户询问公司内部信息、政策、规定、员工手册、内部文档相关内容时，使用此工具检索知识库"""
        try:
            docs = retriever.invoke(query)
            if not docs:
                return "知识库中未找到相关信息"
            return "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            return f"知识库检索失败：{str(e)}"
    return search_knowledge_base


# 静态工具列表（不含需要 retriever 的 search_knowledge_base）
tools = [get_current_time, calculator, web_search, send_email]
