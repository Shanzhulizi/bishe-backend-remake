from datetime import datetime

from sqlalchemy.orm import Session

from app.models.character_usage import CharacterLike


class CharacterLikeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_like_status(self, id, character_id):
        is_liked = self.db.query(CharacterLike).filter(
            CharacterLike.character_id == character_id,
            CharacterLike.user_id == id
        ).first() is not None
        return is_liked

    def batch_get_like_status(self, id, character_ids):
        likes = self.db.query(CharacterLike).filter(
            CharacterLike.character_id.in_(character_ids),
            CharacterLike.user_id == id
        ).all()
        return likes

    def like_character(self, character_id: int, user_id: int):
        """点赞角色"""

        # 记录点赞
        like = CharacterLike(
            character_id=character_id,
            user_id=user_id,
            created_at=datetime.now()  # 🔥 改为普通 datetime，去掉 timezone.utc
        )
        self.db.add(like)
        self.db.commit()

    def unlike_character(self, character_id: int, user_id: int):
        """取消点赞角色"""
        like = self.db.query(CharacterLike).filter(
            CharacterLike.character_id == character_id,
            CharacterLike.user_id == user_id
        ).first()

        if like:
            self.db.delete(like)
            self.db.commit()
