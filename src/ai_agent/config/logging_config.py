"""Structured JSON logging with request_id injection."""
import json
import logging
import sys
from datetime import datetime, timezone


def _get_request_id() -> str:
    """Lazy import to avoid circular dep at module load time."""
    try:
        from ai_agent.api.middleware.auth import REQUEST_ID
        return REQUEST_ID.get("")
    except Exception:
        return ""


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = _get_request_id()
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with JSON output to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 降噪：第三方库过于详细的日志
    for noisy in ("uvicorn.access", "httpx", "langchain", "openai", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
