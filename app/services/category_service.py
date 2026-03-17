# app/services/category_service.py
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session):

        self.category_repo = CategoryRepository(db)








    def get_categories(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """获取类别列表"""
        return self.category_repo.get_all(skip=skip, limit=limit)

    def get_category(self, category_id: int) -> Optional[Category]:
        """获取单个类别"""
        return  self.category_repo.get_by_id(category_id)


    def create_category(self, data: CategoryCreate) -> Category:
        """创建类别"""
        # 检查名称是否已存在

        existing = self.category_repo.get_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail="类别名称已存在")

        category = self.category_repo.create(name=data.name, sort_order=data.sort_order)
        return category

    def update_category(self, category_id: int, data: CategoryUpdate) -> Category:
        """更新类别"""
        category =  self.category_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="类别不存在")

        # 如果要修改名称，检查是否重复
        if not data.name or data.name == category.name:
            raise HTTPException(status_code=400, detail="类别名称错误")
        existing = self.category_repo.get_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail="类别名称已存在")

        category.name = data.name

        if data.sort_order is not None:
            category.sort_order = data.sort_order

        self.category_repo.update(category)
        return category

    def delete_category(self, category_id: int):
        """删除类别"""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="类别不存在")

        # 检查是否有角色在使用这个类别
        usage_count = self.category_repo.count_use(category_id)

        if usage_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"该类别正在被 {usage_count} 个角色使用，无法删除"
            )

        self. category_repo.delete(category)

