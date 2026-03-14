
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.tag_repo import TagRepository
from app.schemas.tag import TagCreate, TagUpdate


class TagService:
    def __init__(self, db: Session):
        self.tag_repo = TagRepository(db)

    def get_tags(self, skip: int = 0, limit: int = 100) -> List[Tag]:
        """获取标签列表"""
        return self.tag_repo.get_all(skip, limit)

    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """获取单个标签"""
        return self.tag_repo.get_by_id(tag_id)

    def create_tag(self, data: TagCreate) -> Tag:
        """创建标签"""
        # 检查名称是否已存在
        existing = self.tag_repo.get_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail="标签名称已存在")
        tag = self.tag_repo.create(name=data.name, sort_order=data.sort_order)
        return tag

    def update_tag(self, tag_id: int, data: TagUpdate) -> Tag:
        """更新标签"""
        tag = self.tag_repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")

        # 如果要修改名称，检查是否重复
        if not data.name or data.name == tag.name:
            raise HTTPException(status_code=400, detail="标签名称错误")
        existing = self.tag_repo.get_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail="标签名称已存在")
        tag.name = data.name

        if data.sort_order is not None:
            tag.sort_order = data.sort_order

        updated_tag = self.tag_repo.update(tag)

        return updated_tag

    def delete_tag(self, tag_id: int):
        """删除标签"""
        tag = self.get_tag(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")

        # 检查是否有角色在使用这个标签
        usage_count = self.tag_repo.count_use(tag_id)

        if usage_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"该标签正在被 {usage_count} 个角色使用，无法删除"
            )
        self.tag_repo.delete(tag)

    def search_tags(self, keyword: str) -> List[Tag]:
        """搜索标签"""
        return self.tag_repo.search(keyword, limit=20)
