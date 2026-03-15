from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field



# 简化的类别信息（用于列表页）
from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse


class CategoryInfo(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# 简化的标签信息（用于列表页）
class TagInfo(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class CharacterCreate(BaseModel):
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    worldview: Optional[str] = None
    voice_id: Optional[str] = None
    greeting: Optional[str] = None
    category_ids: List[int] = Field(default=[])  # 类别ID列表
    tag_ids: List[int] = Field(default=[])  # 标签ID列表
    is_official: bool = False


# 更新角色请求
class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    avatar: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    worldview: Optional[str] = Field(None, max_length=500)
    greeting: Optional[str] = Field(None, max_length=200)
    voice_id: Optional[str] = None
    category_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    is_official: Optional[bool] = None
    is_active: Optional[bool] = None


# class CharacterResponse(BaseModel):
#     id: int
#     name: str
#     avatar: Optional[str] = None
#     description: Optional[str] = None
#     worldview: Optional[str] = None
#     is_active: bool = True
#
#     voice_id: Optional[str] = None
#
#
# class CharacterListItem(BaseModel):
#     id: int
#     name: str
#     avatar: Optional[str] = None
#     description: Optional[str] = None
#     # worldview: Optional[str] = None
#     # tags: List[str] = []
#     like_count: int = 0
#     # is_liked: bool = False
#     usage_count: int = 0
#     chat_count: int = 0
#     popularity_score: float = 0.0  # 热度得分
#     recent_usage: int = 0  # 近期使用数
#
#     # recent_likes: int = 0  # 近期点赞数    # 数据库没有这一项
#     # hot_level: int = 0  # 热度等级 1-5
#
#     class Config:
#         from_attributes = True


# 角色列表项响应（精简版）
class CharacterListItem(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    categories: List[CategoryInfo] = []
    tags: List[TagInfo] = []
    popularity_score: float

    class Config:
        orm_mode = True


# 角色详情响应（完整版）
class CharacterDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    worldview: Optional[str] = None
    avatar: Optional[str] = None
    voice_id: Optional[str] = None
    greeting: Optional[str] = None
    is_official: bool
    is_active: bool

    # 完整类别和标签信息
    categories: List[CategoryResponse] = []
    tags: List[TagResponse] = []

    # 统计信息
    usage_count: int
    chat_count: int
    like_count: int
    popularity_score: float

    # 时间信息
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# 分页响应
class PaginatedResponse(BaseModel):
    total: int
    items: List
    page: int
    size: int
    pages: int