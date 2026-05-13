from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_agent.api.routes.chat import router


@asynccontextmanager
async def lifespan(application: FastAPI):
    # TODO: v1.0 — 使用 LangChain init_chat_model 初始化 LLM
    # TODO: v1.0 — 使用 LangGraph create_react_agent 创建 Agent
    print("[启动] Agent 待实现...")
    application.state.agent = None
    yield
    # 关闭：清理资源
    print("[关闭] 服务停止")


# 创建 FastAPI 注册生命周期事件和路由
app = FastAPI(lifespan=lifespan)
# 前置路由
app.include_router(router, prefix="/api")
