from langchain.agents import create_agent


def react_agent(llm, tools):
    """思考、行动、观察"""
    return create_agent(llm, tools)
