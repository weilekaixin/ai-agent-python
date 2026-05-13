from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_agent.api.routes.chat import router
from ai_agent.core.factory import create_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化 Agent（加载模型、索引知识库）
    print("[启动] 加载 Embedding 模型...")
    app.state.agent = create_agent()
    print("[启动] Agent 就绪，监听端口 8000")
    yield
    # 关闭：清理资源
    print("[关闭] 服务停止")


# 创建 FastAPI 注册生命周期事件和路由
app = FastAPI(lifespan=lifespan)
# 前置路由
app.include_router(router, prefix="/api")
