from langchain.agents import create_agent
from langchain_community.cache import RedisCache
from langchain_core.globals import set_llm_cache
from langchain_core.messages import HumanMessage, AIMessage

from ai_agent.models.prompts import DEFAULT, RAG, QUESTION
from ai_agent.modules.cache.client import get_redis_client
from ai_agent.modules.cache.history import get_history
from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.rag.retriever import get_retriever
from ai_agent.modules.rag.store import build_vector_store
from ai_agent.modules.tool.tools import tools


def create_agent_app():
    """ReAct"""
    # 开启缓存命中
    set_llm_cache(RedisCache(redis_=get_redis_client()))

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


def build_messages_with_history(session_id: str, user_message: str, retriever) -> list:
    """取历史 + 拼 RAG 消息，返回完整消息列表"""
    history = get_history(session_id)
    # 把历史转成 LangChain 消息格式
    messages = []
    for msg in history:
        if msg["role"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))
    # 加上当前问题（带 RAG 检索结果）
    current = build_rag_message(retriever, user_message)
    messages.append(HumanMessage(content=current))
    return messages
