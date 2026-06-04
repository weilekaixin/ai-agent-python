from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_agent.api.routes.chat import router as chat_router
from ai_agent.api.routes.session import router as session_router
from ai_agent.core.factory import create_rag_retriever, setup_llm_cache
from ai_agent.core.graph import create_graph
from ai_agent.modules.db.client import init_db


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    setup_llm_cache()
    retriever = create_rag_retriever("doc/sample.txt")
    # create_graph 是协程，必须 await
    application.state.agent = await create_graph(retriever)
    print("[启动] Agent 就绪")
    yield
    print("[关闭] 服务停止")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "msg": "服务器内部错误"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(chat_router, prefix="/api")
app.include_router(session_router, prefix="/api")
