from typing import Any, AsyncGenerator

from ai_agent.models.constants import *
from ai_agent.modules.llm.deepseek import DeepSeekClient
from ai_agent.modules.memory.store import MemoryStore
from ai_agent.modules.rag.retriever import Retriever
from ai_agent.modules.tool.registry import ToolRegistry


class Agent:
    def __init__(self, registry: ToolRegistry | None = None, retriever: Retriever | None = None):
        self.llm = DeepSeekClient()
        self.memory = MemoryStore()
        self.registry = registry
        self.retriever = retriever

    async def chat(self, message: str) -> AsyncGenerator[str | list[str | Any], Any]:
        # 如果启动了检索功能 先去向量库检索相关内存 拼入上下文帮助大模型理解问题背景
        if self.retriever:
            # 先去检索问题在知识库中的相关信息
            contexts = self.retriever.query(message)
            # 将检索到的相关信息拼接到问题前面 让大模型理解问题背景 注意如果没有检索到相关信息 那么contexts就是空字符串 不会对问题造成干扰
            message = f"{RAG_SYSTEM_PROMPT}{contexts}{QUESTION}{message}"
        # 存储当前问题的记忆到上下文
        self.memory.append(USER_ROLE, message)
        while True:
            # 获取上下文
            messages = self.memory.recent()
            # registry != null ? registry.get_openai_tools() : null
            tools = self.registry.get_openai_tools() if self.registry else None
            # 相当于一个数据有两个值 我只想获取第一个 不关心第二个 调度大模型 注意如果大模型需要使用工具那么回复内容会为空「思考」
            full_reply = EMPTY_STR
            # 流式拼接token
            async for token in self.llm.astream_chat(messages, tools):
                full_reply += token
                yield token
            # 判断大模型是否有使用工具的意图
            if not self.llm.tool_calls:
                # 如果没有使用工具的意图 那么就把大模型的回复当做最终回复 存储到记忆中 然后结束本次对话
                self.memory.append(ASSISTANT_ROLE, full_reply)
                return
            # 如果有使用工具的意图 那么就把大模型的回复当做思考过程 存储到记忆中 然后调用工具
            self.memory.append_tool_calls(self.llm.tool_calls)
            for tc in self.llm.tool_calls:
                assert self.registry
                # 使用工具获取结果「行动」
                result = self.registry.execute(tc[NAME], **tc[ARGS])
                # 存入上下文让大模型自己决定
                self.memory.append(TOOL_ROLE, result, tc[ID])
