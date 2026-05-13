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

    async def chat(self, message: str) -> str:
        # 如果启动了检索功能 先去向量库检索相关内存 拼入上下文帮助大模型理解问题背景
        if self.retriever:
            # 先去检索问题在知识库中的相关信息
            contexts = self.retriever.query(message)
            # 将检索到的相关信息拼接到问题前面 让大模型理解问题背景 注意如果没有检索到相关信息 那么contexts就是空字符串 不会对问题造成干扰
            message = f"{RAG_SYSTEM_PROMPT}{contexts}{QUESTION}{message}"
        # 存储当前问题的记忆到上下文
        self.memory.append(USER_ROLE, message)
        # 获取上下文
        messages = self.memory.recent()
        # registry != null ? registry.get_openai_tools() : null
        tools = self.registry.get_openai_tools() if self.registry else None
        # 相当于一个数据有两个值 我只想获取第一个 不关心第二个 调度大模型 注意如果大模型需要使用工具那么回复内容会为空「思考」
        reply, tool_calls = await self.llm.chat(messages, tools)
        # 如果大模型需要调用工具 那么就进入循环 直到他不需要为止
        while tool_calls:
            # 大模型决定调工具，把指令存入上下文
            self.memory.append_tool_calls(tool_calls)
            # 循环工具列表
            for tc in tool_calls:
                # 断言抑制IDE提示 实际如果没有注册 那么大模型根本不会tool_calls
                assert self.registry
                # 使用工具获取结果「行动」
                result = self.registry.execute(tc[NAME], **tc[ARGS])
                # 存入上下文让大模型自己决定
                self.memory.append(TOOL_ROLE, result, tc[ID])
            # 刷新大模型上下文
            messages = self.memory.recent()
            # 拿到包含结果的上下文后再次询问大模型「观察」
            reply, tool_calls = await self.llm.chat(messages, tools)
        # 将大模型的回复存入上下文
        self.memory.append(ASSISTANT_ROLE, reply)
        return reply
