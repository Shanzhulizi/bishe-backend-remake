# 替换异步引擎为同步引擎
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

print(settings.DATABASE_URL)
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
