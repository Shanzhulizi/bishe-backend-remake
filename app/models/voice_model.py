# app/models/voice_model.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float
from sqlalchemy.sql import func

from app.db import Base


class VoiceModel(Base):
    """声音模型 - 存储从音频提取的特征"""
    __tablename__ = "voice_models"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 基本信息
    name = Column(String(100), nullable=False)  # 模型名称
    description = Column(Text)  # 描述
    language = Column(String(10), default="zh")  # 语言

    # 唯一标识
    model_code = Column(String(100), unique=True, nullable=False)  # 例如: model_xxxxx

    # 文件路径
    sample_file = Column(String(200))  # 原始音频样本路径
    model_file = Column(String(200))  # 提取的特征模型文件路径 (.pth 或 .pt)
    preview_audio = Column(String(200))  # 预览音频路径

    # 模型元数据
    duration = Column(Float)  # 音频时长（秒）
    speaker_embedding = Column(Text)  # 说话者特征（可存为JSON）

    # 状态
    status = Column(String(20), default="processing")  # processing, completed, failed
    error_message = Column(Text, nullable=True)

    # 使用统计
    use_count = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 是否可用
    is_active = Column(Boolean, default=True)