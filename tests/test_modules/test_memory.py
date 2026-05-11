import asyncio

from ai_agent.models.constants import USER_ROLE, ASSISTANT_ROLE
from ai_agent.modules.memory.store import MemoryStore
from ai_agent.modules.llm.deepseek import DeepSeekClient


async def test_memory():
    store = MemoryStore()
    client = DeepSeekClient()

    while True:
        content = input("\n>>> ")
        if content.strip() == "/exit":
            break

        store.append(USER_ROLE, content)
        chunks = []
        async for chunk in client.client.astream(store.recent()):
            print(chunk.content, end="", flush=True)
            chunks.append(chunk.content)
        store.append(ASSISTANT_ROLE, "".join(chunks))
        print()


if __name__ == "__main__":
    asyncio.run(test_memory())
