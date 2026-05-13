import os
import asyncio

from ai_agent.modules.rag.splitter import RecursiveSplitter
from ai_agent.modules.rag.embedder import Embedder
from ai_agent.modules.rag.retriever import Retriever
from ai_agent.core.agent import Agent


async def test_rag():
    # 1. 读文件
    base_dir = os.path.dirname(os.path.dirname(__file__))  # tests/
    project_dir = os.path.dirname(base_dir)  # 项目根目录
    with open(os.path.join(project_dir, "data", "sample.txt"), encoding="utf-8") as f:
        text = f.read()

    # 2. 切片
    splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split(text)
    print(f"切成了 {len(chunks)} 段：")
    for i, c in enumerate(chunks):
        print(f"  [{i}] {c}")

    # 3. 向量化 + 存入检索器
    embedder = Embedder()
    retriever = Retriever(embedder)
    retriever.add(chunks)

    # 4. 提问，看看能召回什么
    question = "什么是深度学习？"
    results = retriever.query(question, top_k=2)
    print(f"\n问题：{question}")
    print("召回结果：")
    for r in results:
        print(f"  - {r}")


async def test_agent_with_rag():
    # 1. 读文件
    base_dir = os.path.dirname(os.path.dirname(__file__))
    project_dir = os.path.dirname(base_dir)
    with open(os.path.join(project_dir, "data", "sample.txt"), encoding="utf-8") as f:
        text = f.read()

    # 2. 切片
    splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split(text)
    print(f"切片完成：{len(chunks)} 段")

    # 3. 加载 Embedding 模型（第一次会下载，较慢）
    print("加载 Embedding 模型...")
    retriever = Retriever(Embedder())
    print("向量化并存入检索器...")
    retriever.add(chunks)
    print("检索器准备完成")

    # 4. 创建 Agent + 提问
    print("创建 Agent...")
    agent = Agent(retriever=retriever)
    print("调用 DeepSeek API...")
    reply = await agent.chat("天网系统的负责人是谁？他什么时候入职的？")
    print(f"\nAI: {reply}")


if __name__ == "__main__":
    asyncio.run(test_agent_with_rag())
