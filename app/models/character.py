from sqlalchemy import Column, BigInteger, String, Text, Boolean, TIMESTAMP, func, Integer, Float
from sqlalchemy.orm import relationship

from app.db.base import Base  # declarative_base


from sqlalchemy import Column, BigInteger, String, Text, Boolean, Integer, Float, TIMESTAMP, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func




# 关联表
character_categories = Table(
    'character_categories',
    Base.metadata,
    Column('character_id', BigInteger, ForeignKey('character.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)

character_tags = Table(
    'character_tags',
    Base.metadata,
    Column('character_id', BigInteger, ForeignKey('character.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


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




    # 新增统计字段
    usage_count = Column(Integer, default=0, nullable=False)  # 使用人数
    chat_count = Column(Integer, default=0, nullable=False)  # 对话次数
    like_count = Column(Integer, default=0, nullable=False)  # 点赞人数
    recent_usage_count = Column(Integer, default=0, nullable=False)  # 最近使用人数
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)  # 最后使用时间

    # 可选：热度得分（可定时计算）
    popularity_score = Column(Float, default=0.0, nullable=False)

    voice_id = Column(String(64), nullable=True)  # 存储声音代码

    greeting = Column(Text, nullable=True)  # 开场白
    is_official= Column(Boolean, default=False, nullable=False)  # 是否官方角色

    # 关联关系
    categories = relationship("Category", secondary=character_categories, backref="characters")
    tags = relationship("Tag", secondary=character_tags, backref="characters")
