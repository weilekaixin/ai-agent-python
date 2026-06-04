from contextlib import contextmanager

from sqlmodel import SQLModel, Session, create_engine

from ai_agent.config.settings import settings
from ai_agent.modules.db import models  # noqa: F401

# pool_size: 连接池大小；max_overflow: 超出 pool_size 后最多再开多少个连接
engine = create_engine(settings.postgres_url, echo=False, pool_size=10, max_overflow=20)


def init_db():
    """初始化数据库，建表（有则跳过）"""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    """数据库会话上下文管理器，自动提交/回滚/关闭"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
