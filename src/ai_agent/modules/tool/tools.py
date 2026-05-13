from datetime import datetime

from langchain_core.tools import tool


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


# 工具列表
tools = [get_current_time, calculator]
