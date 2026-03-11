







from typing import Optional

from pydantic import BaseModel


# 1. 定义 Pydantic 模型（用于序列化）
class CharacterRecommendResponse(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None  # 允许为空
    description: Optional[str] = None
    popularity_score: float
    like_count: int
    usage_count: int
    chat_count: int

    # 配置支持从 ORM/Row 对象转换
    class Config:
        from_attributes = True

