import logging
from contextlib import asynccontextmanager

import redis as redis_lib
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ai_agent.api.middleware.auth import ApiKeyMiddleware, RequestIdMiddleware
from ai_agent.api.middleware.rate_limit import RateLimitMiddleware
from ai_agent.api.routes.chat import router as chat_router
from ai_agent.api.routes.multi_agent import router as multi_agent_router
from ai_agent.api.routes.persona import router as persona_router
from ai_agent.api.routes.session import router as session_router
from ai_agent.api.routes.structured import router as structured_router
from ai_agent.config.logging_config import setup_logging
from ai_agent.config.settings import settings
from ai_agent.core.factory import create_rag_retriever, setup_llm_cache
from ai_agent.core.graph import create_graph
from ai_agent.modules.db.client import init_db, engine
from ai_agent.modules.memory.dreaming import dream

# 尽早配置日志，确保所有模块的日志输出都是 JSON 格式
setup_logging(settings.log_level)
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


app = FastAPI(
    lifespan=lifespan,
    title="AI Agent API",
    description="LangGraph-powered AI agent with memory, skills and human-in-the-loop",
    version="1.0.0",
)

# Middleware stack (last added = outermost = executes first):
# CORSMiddleware → RateLimitMiddleware → RequestIdMiddleware → ApiKeyMiddleware → route
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware, enabled=settings.rate_limit_enabled)
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


@app.get("/health", tags=["ops"])
async def health(req: Request):
    """Deep health check for k8s readiness/liveness probes."""
    checks: dict[str, str] = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "error"

    try:
        r = redis_lib.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password or None,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        r.close()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    checks["agent"] = "ok" if getattr(req.app.state, "agent", None) else "not_ready"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        {"status": "ok" if all_ok else "degraded", **checks},
        status_code=200 if all_ok else 503,
    )


@app.post("/api/dream", tags=["ops"])
async def trigger_dream():
    """Manually trigger nightly memory consolidation."""
    result = await dream()
    return {"status": result}


app.include_router(chat_router, prefix="/api")
app.include_router(session_router, prefix="/api")
app.include_router(persona_router, prefix="/api")
app.include_router(structured_router, prefix="/api")
app.include_router(multi_agent_router, prefix="/api")
