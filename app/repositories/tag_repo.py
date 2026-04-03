from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import character_tags
from app.models.tag import Tag


class TagRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tag_id: int) -> Optional[Tag]:
        stmt = select(Tag).where(Tag.id == tag_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Tag]:
        stmt = select(Tag).where(Tag.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Tag]:
        stmt = select(Tag).order_by(Tag.sort_order, Tag.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, name: str, sort_order: int = 0) -> Tag:
        tag = Tag(name=name, sort_order=sort_order, created_at=datetime.now())
        self.db.add(tag)
        await self.db.flush()
        await self.db.refresh(tag)
        return tag

    async def update(self, tag: Tag) -> Tag:
        """更新标签"""
        self.db.add(tag)
        await self.db.flush()
        await self.db.refresh(tag)
        return tag

    async def delete(self, tag: Tag) -> bool:
        await self.db.delete(tag)
        await self.db.flush()
        return True

    async def count_use(self, tag_id: int) -> int:
        """统计标签被多少角色使用"""
        stmt = select(func.count()).select_from(character_tags).where(
            character_tags.c.tag_id == tag_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def search(self, keyword: str, limit: int = 20) -> List[Tag]:
        stmt = select(Tag).where(
            Tag.name.ilike(f"%{keyword}%")
        ).order_by(Tag.sort_order).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
