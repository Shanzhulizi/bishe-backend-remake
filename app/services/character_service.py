from app.core.logging import get_logger
from app.repositories.character_repo import CharacterRepository

logger = get_logger(__name__)
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional

from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate


class CharacterService:
    def __init__(self, db: Session):
        self.db = db
        self.character_repo = CharacterRepository(db)

    def get_characters(
            self,
            skip: int = 0,
            limit: int = 20,
            category_id: Optional[int] = None,
            tag_id: Optional[int] = None,
            keyword: Optional[str] = None,
            is_official: Optional[bool] = None
    ) -> tuple[List[Character], int]:
        """获取角色列表（支持筛选和搜索）"""

        characters, total = self.character_repo.get_all(skip, limit, category_id, tag_id, keyword, is_official)

        return characters, total

    def get_character(self, character_id: int) -> Optional[Character]:
        """获取单个角色详情"""
        return self.character_repo.get_by_id_with_relations(character_id)

    def create_character(self, data: CharacterCreate) -> Character:
        """创建角色"""

        # 不检查名称是否已经存在，允许重复名称，鼓励用户创作
        # existing = self.db.query(Character).filter(
        #     Character.name == data.name
        # ).first()
        # if existing:
        #     raise HTTPException(status_code=400, detail="角色名称已存在")

        # 创建角色
        character  = self.character_repo.create_with_relations(data)
        return character

    def update_character(self, character_id: int, data: CharacterUpdate) -> Character:
        """更新角色"""

        # 2. 转换为字典
        update_data = data.dict(exclude_unset=True)

        # 3. 调用 repo 更新
        character = self.character_repo.update_complete(character_id, update_data)

        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")

        # 4. 提交事务
        self.db.commit()
        self.db.refresh(character)

        return character

    def delete_character(self, character_id: int):
        """删除角色（软删除）"""
        is_deleted = self.character_repo.soft_delete(character_id)
        if not is_deleted:
            raise HTTPException(status_code=404, detail="删除错误")
        self.db.commit()

    def get_character_like_count(self,character_id) -> int:
        """获取角色的点赞数"""
        return self.character_repo.get_like_count(character_id)