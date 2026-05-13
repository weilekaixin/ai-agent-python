from ai_agent.config.settings import BASE_DIR
from ai_agent.core.agent import Agent
from ai_agent.modules.rag.embedder import Embedder
from ai_agent.modules.rag.retriever import Retriever
from ai_agent.modules.rag.splitter import RecursiveSplitter
from ai_agent.modules.tool.registry import ToolRegistry
from ai_agent.modules.tool.tools import GetTimeTool, CalculatorTool


def create_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GetTimeTool())
    registry.register(CalculatorTool())
    return registry


def create_retriever() -> Retriever:
    with open(BASE_DIR / "doc" / "sample.txt", encoding="utf-8") as f:
        text = f.read()
    splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split(text)
    retriever = Retriever(Embedder())
    retriever.add(chunks)
    return retriever


def create_agent() -> Agent:
    return Agent(
        registry=create_registry(),
        retriever=create_retriever()
    )
