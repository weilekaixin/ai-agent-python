import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_agent.api.middleware.auth import ApiKeyMiddleware, RequestIdMiddleware
from ai_agent.api.routes.chat import router as chat_router
from ai_agent.api.routes.session import router as session_router
from ai_agent.core.factory import create_rag_retriever, setup_llm_cache
from ai_agent.core.graph import create_graph
from ai_agent.modules.db.client import init_db
from ai_agent.modules.memory.dreaming import dream

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    setup_llm_cache()
    retriever = create_rag_retriever("doc/sample.txt")
    application.state.agent = await create_graph(retriever)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(dream, "cron", hour=2, minute=0)
    scheduler.start()
    application.state.scheduler = scheduler
    logger.info("Agent ready, AutoDream scheduler started")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Service shutting down")


app = FastAPI(lifespan=lifespan)

# 顺序很重要: CORS 必须最外层，再是 RequestId，最后是 ApiKey
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/dream")
async def trigger_dream():
    result = await dream()
    return {"status": result}


app.include_router(chat_router, prefix="/api")
app.include_router(session_router, prefix="/api")
