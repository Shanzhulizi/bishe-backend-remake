from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.character import Character
from app.repositories.character_like_repo import CharacterLikeRepository
from app.repositories.character_repo import CharacterRepository


class CharacterLikeService:
    def __init__(self, db: Session):
        self.db = db
        self.character_like_repo = CharacterLikeRepository(self.db)
        self.character_repo = CharacterRepository(self.db)

    def like_character(self, character_id: int, user_id: int):
        """点赞角色"""
        self.character_like_repo.like_character(character_id, user_id)
        # 更新点赞数
        self.character_repo.increment_like_count(character_id)
        self.db.commit()

    def unlike_character(self, character_id: int, user_id: int) -> bool:
        """
        取消点赞
        Returns:
            bool: 是否成功（False表示还没点赞）
        """
        self.character_like_repo.unlike_character(character_id, user_id)

        # 更新角色的点赞数
        self.character_repo.decrement_like_count(character_id)
        self.db.commit()
        return True

    def get_character_like_status(self, user_id, character_id):
        return self.character_like_repo.get_like_status(user_id, character_id)

    def batch_get_like_status(self, current_user, character_ids):
        # 查询当前用户对所有角色的点赞记录
        likes = self.character_like_repo.batch_get_like_status(current_user.id, character_ids)
        # 构建点赞状态映射
        liked_map = {like.character_id: True for like in likes}

        # 确保所有请求的 ID 都在返回结果中（未点赞的默认为 False）
        for char_id in character_ids:
            if char_id not in liked_map:
                liked_map[char_id] = False
        return liked_map
