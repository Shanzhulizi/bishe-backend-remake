# app/services/behavior_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.behavior_repo import BehaviorRepository

logger = get_logger(__name__)


class BehaviorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.behavior_repo  = BehaviorRepository(db)

    async def record_view(self, user_id: int, character_id: int):
        """记录浏览"""
        logger.info(f"记录浏览行为 - 用户ID: {user_id}, 角色ID: {character_id}")
        record = self.behavior_repo.get_behavior(user_id, character_id, 'VIEW')
        if not record:
            # 只有当天没有浏览记录才记录浏览行为，避免重复记录
            await self.behavior_repo.record_view(user_id, character_id)
            return True
        return False

    async def record_chat(self, user_id: int, character_id: int):
        """记录聊天"""
        logger.info(f"记录聊天行为 - 用户ID: {user_id}, 角色ID: {character_id}")
        await self.behavior_repo.record_chat(user_id, character_id)

    async def record_like(self, user_id: int, character_id: int):
        """记录点赞"""
        logger.info(f"记录点赞行为 - 用户ID: {user_id}, 角色ID: {character_id}")
        await self.behavior_repo.record_like(user_id, character_id)

    async def delete_records(self, user_id: int, character_id: int, behavior_type: str):
        """删除用户行为记录"""
        logger.info(f"删除用户行为记录 - 用户ID: {user_id}, 角色ID: {character_id}, 行为类型: {behavior_type}")
        await self.behavior_repo.delete_records(user_id, character_id, behavior_type)

    async def get_like_record(self, user_id: int, character_id: int):
        """获取用户点赞行为记录"""
        logger.info(f"获取用户行为记录 - 用户ID: {user_id}, 角色ID: {character_id}")
        return await self.behavior_repo.get_like_record(user_id, character_id)
