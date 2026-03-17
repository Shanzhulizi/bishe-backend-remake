# app/schemas/tag.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    sort_order: int = 0


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    sort_order: Optional[int] = None


class TagResponse(TagBase):
    id: int
    created_at: datetime

    # 统计信息（可选）
    character_count: Optional[int] = 0

    class Config:
        orm_mode = True