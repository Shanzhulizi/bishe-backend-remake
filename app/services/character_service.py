from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.behavior_repo import BehaviorRepository
from app.repositories.character_repo import CharacterRepository

logger = get_logger(__name__)
from fastapi import HTTPException
from typing import List, Optional

from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate


class CharacterService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.character_repo = CharacterRepository(db)
        self.behavior_repo = BehaviorRepository(db)

    async def get_characters(
            self,
            skip: int = 0,
            limit: int = 20,
            category_id: Optional[int] = None,
            tag_id: Optional[int] = None,
            keyword: Optional[str] = None,
            is_official: Optional[bool] = None
    ) -> tuple[List[Character], int]:
        """获取角色列表（支持筛选和搜索）"""

        characters, total =await  self.character_repo.get_all(skip, limit, category_id, tag_id, keyword, is_official)

        return characters, total

    async def get_character(self, character_id: int) -> Optional[Character]:
        """获取单个角色详情"""
        return await  self.character_repo.get_by_id_with_relations(character_id)

    async def create_character(self, data: CharacterCreate) -> Character:
        """创建角色"""

        character =await self.character_repo.create_with_relations(data)
        return character

    async def update_character(self, character_id: int, data: CharacterUpdate) -> Character:
        """更新角色"""
        # 转换为字典
        update_data = data.dict(exclude_unset=True)
        # 调用 repo 更新
        character =await self.character_repo.update_complete(character_id, update_data)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        # 提交事务
        await self.db.flush()
        return character

    async def delete_character(self, character_id: int):
        """删除角色（软删除）"""
        is_deleted =await self.character_repo.soft_delete(character_id)
        if not is_deleted:
            raise HTTPException(status_code=404, detail="删除错误")
        await self.db.commit()

    async def get_character_like_count(self, character_id) -> int:
        """获取角色的点赞数"""
        return await self.character_repo.get_like_count(character_id)

    async def get_character_chat_count(self, character_id) -> int:
        """获取角色的聊天数"""
        return await self.behavior_repo.get_chats_count(character_id)

    async def increment_like_count(self, character_id: int):
        """点赞角色"""
        logger.info(f"更新角色点赞数: character_id={character_id}")
        await self.character_repo.increment_like_count(character_id)

    async def decrement_like_count(self, character_id: int) -> bool:
        """
        取消点赞
        Returns:
            bool: 是否成功（False表示还没点赞）
        """
        logger.info(f"更新角色点赞数: character_id={character_id}")
        await self.character_repo.decrement_like_count(character_id)
        return True

    async def get_character_like_status(self, user_id, character_id):
        """获取用户对角色的点赞状态"""
        return await self.behavior_repo.get_like_status(user_id, character_id)

    async def batch_get_like_status(self, current_user, character_ids):
        """批量获取用户对多个角色的点赞状态"""
        # 查询当前用户对所有角色的点赞记录
        likes =await  self.behavior_repo.batch_get_like_status(current_user.id, character_ids)
        # 构建点赞状态映射
        liked_map = {like.character_id: True for like in likes}

        # 确保所有请求的 ID 都在返回结果中（未点赞的默认为 False）
        for char_id in character_ids:
            if char_id not in liked_map:
                liked_map[char_id] = False
        return liked_map

    async def increment_view_count(self, character_id: int):
        """增加角色的浏览数（每次访问角色详情时调用）"""
        logger.info(f"更新角色点赞数: character_id={character_id}")
        await self.character_repo.increment_view_count(character_id)

    async def increment_chat_count(self, character_id):
        logger.info(f"更新角色聊天数: character_id={character_id}")
        await self.character_repo.increment_chat_count(character_id)

    async def update_use_time(self, character_id):
        logger.info(f"更新角色使用时间: character_id={character_id}")
        updated = CharacterUpdate(last_used_at=datetime.now(timezone.utc))
        await self.update_character(character_id, updated)
