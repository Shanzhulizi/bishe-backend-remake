# app/schemas/category.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    # 统计信息（可选）
    character_count: Optional[int] = 0

    class Config:
        orm_mode = True