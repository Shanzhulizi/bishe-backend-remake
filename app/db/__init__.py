# app/db/init_db.py
from app.db.base import Base
from app.db.session import async_engine


def init_db():
    Base.metadata.create_all(bind=async_engine)
