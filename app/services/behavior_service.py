# app/services/behavior_service.py
from sqlalchemy.orm import Session
from app.models.user_behavior import UserBehavior
from datetime import datetime


class BehaviorService:
    def __init__(self, db: Session):
        self.db = db

    def record_view(self, user_id: int, character_id: int):
        """记录浏览"""
        behavior = UserBehavior(
            user_id=user_id,
            character_id=character_id,
            behavior_type='view',
            created_at=datetime.now()
        )
        self.db.add(behavior)
        self.db.commit()

    def record_chat(self, user_id: int, character_id: int):
        """记录聊天"""
        behavior = UserBehavior(
            user_id=user_id,
            character_id=character_id,
            behavior_type='chat',
            created_at=datetime.now()
        )
        self.db.add(behavior)
        self.db.commit()

    def record_like(self, user_id: int, character_id: int):
        """记录点赞"""
        behavior = UserBehavior(
            user_id=user_id,
            character_id=character_id,
            behavior_type='like',
            created_at=datetime.now()
        )
        self.db.add(behavior)
        self.db.commit()