from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.character import character_categories


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Category]:
        result = await self.db.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        result = await self.db.execute(
            select(Category)
                .order_by(Category.sort_order, Category.id)
                .offset(skip)
                .limit(limit)
        )
        return result.scalars().all()

    async def create(self, name: str, sort_order: int = 0) -> Category:
        category = Category(name=name, sort_order=sort_order)
        self.db.add(category)
        await self.db.flush()  # 获取ID
        return category

    async def delete(self, category: Category) -> bool:
        await self.db.delete(category)

        return True

    async def count_use(self, category_id: int) -> int:
        """统计类别被多少角色使用"""

        result = await self.db.execute(
            select(func.count(character_categories.c.character_id))
                .where(character_categories.c.category_id == category_id)
        )
        return result.scalar() or 0
