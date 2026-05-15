from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_agent.api.routes.chat import router
from ai_agent.core.factory import create_agent_app, create_rag_retriever
from ai_agent.modules.db.client import init_db


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    application.state.agent = create_agent_app()
    application.state.retriever = create_rag_retriever("doc/sample.txt")
    print("[启动] Agent 就绪")
    yield
    print("[关闭] 服务停止")


# 创建 FastAPI 注册生命周期事件和路由
app = FastAPI(lifespan=lifespan)
# 前置路由
app.include_router(router, prefix="/api")
