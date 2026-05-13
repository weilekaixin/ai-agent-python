import os
import asyncio

from ai_agent.core.agent import Agent
from ai_agent.modules.rag.splitter import RecursiveSplitter
from ai_agent.modules.rag.embedder import Embedder
from ai_agent.modules.rag.retriever import Retriever
from ai_agent.modules.tool.registry import ToolRegistry
from ai_agent.modules.tool.tools import GetTimeTool, CalculatorTool


# ===== 初始化工具 =====
def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GetTimeTool())
    registry.register(CalculatorTool())
    return registry


# ===== 初始化 RAG 索引 =====
def build_retriever() -> Retriever:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    project_dir = os.path.dirname(base_dir)
    with open(os.path.join(project_dir, "data", "sample.txt"), encoding="utf-8") as f:
        text = f.read()
    splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split(text)
    retriever = Retriever(Embedder())
    retriever.add(chunks)
    return retriever


async def test_chat_only():
    """纯对话"""
    agent = Agent()
    async for token in agent.chat("讲个笑话，20个字以内"):
        print(token, end="", flush=True)
    print("\n")


async def test_chat_with_tools():
    """对话 + 工具"""
    agent = Agent(registry=build_registry())
    async for token in agent.chat("现在几点？顺便算一下 3+5*2等于多少"):
        print(token, end="", flush=True)
    print("\n")


async def test_chat_with_rag():
    """对话 + RAG"""
    agent = Agent(retriever=build_retriever())
    async for token in agent.chat("什么是深度学习？"):
        print(token, end="", flush=True)
    print("\n")


async def test_chat_with_tools_and_rag():
    """对话 + 工具 + RAG（全功能）"""
    agent = Agent(
        registry=build_registry(),
        retriever=build_retriever()
    )

    # 既需要从文档里找信息，又需要用到工具计算
    question = "张三是谁？工号多少？再用计算器算一下他的工号加1000等于多少"
    print(f"问题：{question}\n")
    print("回答：", end="", flush=True)
    async for token in agent.chat(question):
        print(token, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(test_chat_with_tools_and_rag())
