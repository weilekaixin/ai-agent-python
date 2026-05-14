from sqlmodel import SQLModel, Session, create_engine

from ai_agent.config.settings import settings
from ai_agent.modules.db import models  # noqa: F401

# 模块级全局变量 创建数据库连接池 echo：sql打印
engine = create_engine(settings.postgres_url, echo=False)


def init_db():
    """初始化数据库，建表"""
    # sqlmodel 满足SQLModel, table=True的会去扫描已有的表 有则跳过 无则创建 不会对数据造成影响
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """获取数据库会话"""
    # 数据库连接
    return Session(engine)
