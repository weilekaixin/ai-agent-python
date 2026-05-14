from langchain.agents import create_agent

from ai_agent.models.prompts import DEFAULT, RAG, QUESTION
from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.rag.retriever import get_retriever
from ai_agent.modules.rag.store import build_vector_store
from ai_agent.modules.tool.tools import tools


def create_agent_app():
    """ReAct"""
    llm = get_llm()
    agent = create_agent(llm, tools, system_prompt=DEFAULT)
    return agent


def create_rag_retriever(file_path: str):
    """建向量库，返回检索器"""
    store = build_vector_store(file_path)
    return get_retriever(store)


def build_rag_message(retriever, user_message: str) -> str:
    """检索相关内容，拼接成带资料的问题"""
    docs = retriever.invoke(user_message)
    context = "\n".join([doc.page_content for doc in docs])
    return f"{RAG}\n{context}{QUESTION}{user_message}"
