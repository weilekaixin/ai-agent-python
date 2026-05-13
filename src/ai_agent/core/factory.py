from langchain.agents import create_agent

from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.tool.tools import tools


def create_agent_app():
    """ReAct"""
    llm = get_llm()
    agent = create_agent(llm, tools)
    return agent
