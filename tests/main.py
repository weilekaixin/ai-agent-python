from langchain_core.messages import HumanMessage

from ai_agent.core.graph import create_graph

if __name__ == '__main__':
    # 获取图
    graph = create_graph()
    # 调用图
    result = graph.invoke({"messages": [HumanMessage(content="今天北京的天气怎么样")]})
    # 打印最后一条消息
    print(result["messages"][-1].content)
