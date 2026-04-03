from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

# print(settings.DATABASE_URL)
async_engine = create_async_engine(
    # settings.DATABASE_URL,
    settings.ASYNC_DATABASE_URL,
    echo=False,
    pool_size=20,  # 连接池大小（根据并发量调整）
    max_overflow=40,  # 最大溢出连接数
    pool_timeout=30,  # 获取连接超时（秒）
    pool_recycle=3600,  # 1小时回收连接
    pool_pre_ping=True,  # 使用前检查连接
    pool_use_lifo=True,  # 后进先出，提高热点连接利用率
)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)