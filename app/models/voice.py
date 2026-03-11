from sqlalchemy import create_engine, Column, String, DateTime, Float, Text, BigInteger, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Voice(Base):
    """声音模型 - 存储参考声音信息"""
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    voice_id = Column(String(64), unique=True, index=True)
    voice_name = Column(String(100))
    voice_text = Column(Text)
    voice_url = Column(String(255))  # 确保有这个字段
    duration = Column(Float)
    sample_rate = Column(Integer, nullable=True)  # 如果有默认值，可以设置 nullable=True
    user_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, server_default=func.now())






