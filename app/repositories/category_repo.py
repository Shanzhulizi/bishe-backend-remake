from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        return self.db.query(Category) \
            .order_by(Category.sort_order, Category.id) \
            .offset(skip) \
            .limit(limit) \
            .all()

    def create(self, name: str, sort_order: int = 0) -> Category:
        category = Category(name=name, sort_order=sort_order,created_at =func.now())
        self.db.add(category)
        self.db.flush()
        return category

    def update(self, category: Category) -> Optional[        Category]:

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> bool:
        self.db.delete(category)
        self.db.commit()
        return True
    def count_use(self, category_id: int) -> int:
        """统计类别被多少角色使用"""
        from app.models.character import character_categories
        count = self.db.query(func.count(character_categories.c.character_id)) \
            .filter(character_categories.c.category_id == category_id) \
            .scalar()
        return count or 0