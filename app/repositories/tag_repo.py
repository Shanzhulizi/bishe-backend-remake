from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.tag import Tag


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        return self.db.query(Tag).filter(Tag.id == tag_id).first()

    def get_by_name(self, name: str) -> Optional[Tag]:
        return self.db.query(Tag).filter(Tag.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Tag]:
        return self.db.query(Tag) \
            .order_by(Tag.sort_order, Tag.id) \
            .offset(skip) \
            .limit(limit) \
            .all()

    def create(self, name: str, sort_order: int = 0) -> Tag:
        tag = Tag(name=name, sort_order=sort_order, created_at=datetime.now())
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update(self, tag: Tag) -> Tag:
        """更新标签"""
        self.db.add(tag)
        self.db.commit()  # ✅ repo 里 commit
        self.db.refresh(tag)
        return tag

    def delete(self, tag: Tag) -> bool:
        self.db.delete(tag)
        self.db.commit()
        return True

    def count_use(self, tag_id: int) -> int:
        """统计标签被多少角色使用"""
        from app.models.character import character_tags
        return self.db.query(character_tags).filter(character_tags.c.tag_id == tag_id).count()

    def search(self, keyword: str, limit: int = 20) -> List[Tag]:
        return self.db.query(Tag).filter(
            Tag.name.ilike(f"%{keyword}%")
        ).order_by(Tag.sort_order).limit(limit).all()
