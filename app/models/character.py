from sqlalchemy import Column, BigInteger, String, Text, Boolean, TIMESTAMP, func, Integer, Float
from sqlalchemy.orm import relationship

from app.db.base import Base  # declarative_base


class Character(Base):
    __tablename__ = "character"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    worldview = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    avatar = Column(Text, nullable=True)  # 👈 新增
    voice_style = Column(
        String(32),
        nullable=False,
        default="default"
    )


    # voice_code = Column(String(50), nullable=True)  # 存储声音代码
    voice_id = Column(String(64), nullable=True)  # 存储声音代码
    voice_name = Column(String(50), nullable=True)  # 存储声音名称（可选）

    # 新增统计字段
    usage_count = Column(Integer, default=0, nullable=False)  # 使用人数
    chat_count = Column(Integer, default=0, nullable=False)  # 对话次数
    like_count = Column(Integer, default=0, nullable=False)  # 点赞人数
    recent_usage_count = Column(Integer, default=0, nullable=False)  # 最近使用人数
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)  # 最后使用时间

    # 可选：热度得分（可定时计算）
    popularity_score = Column(Float, default=0.0, nullable=False)

    # 关联角色配置
    config = relationship(
        "CharacterConfigs",
        uselist=False,
        back_populates="character",
        cascade="all, delete-orphan"
    )
