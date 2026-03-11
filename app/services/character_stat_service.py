# services/character_stat_service.py
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.character import Character
from app.models.character_usage import CharacterUsageLog, CharacterLike
from app.repositories.character_like_repo import CharacterLikeRepository


class CharacterStatService:

    @staticmethod
    def record_chat(db: Session, character_id: int, user_id: int):
        """记录一次对话"""
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            return

        # 对话次数 +1
        character.chat_count += 1

        # 🔥 修改这里：使用普通 datetime，不带时区
        now = datetime.now()  # 改为普通 datetime
        today_start = datetime(now.year, now.month, now.day)  # 去掉 tzinfo
        today_end = today_start + timedelta(days=1)

        # 记录使用（每天每个用户只计一次）
        usage_log = db.query(CharacterUsageLog).filter(
            CharacterUsageLog.character_id == character_id,
            CharacterUsageLog.user_id == user_id,
            CharacterUsageLog.created_at >= today_start,
            CharacterUsageLog.created_at < today_end
        ).first()

        if not usage_log:
            # 今日第一次使用
            log = CharacterUsageLog(
                character_id=character_id,
                user_id=user_id,
                created_at=now  # 普通 datetime
            )
            db.add(log)

            # 更新使用人数
            character.usage_count += 1

            # 更新最近使用人数（最近7天）
            seven_days_ago = now - timedelta(days=7)
            recent_users = db.query(CharacterUsageLog.user_id).filter(
                CharacterUsageLog.character_id == character_id,
                CharacterUsageLog.created_at >= seven_days_ago
            ).distinct().count()
            character.recent_usage_count = recent_users

        character.last_used_at = now
        db.commit()

    @staticmethod
    def like_character(db: Session, character_id: int, user_id: int):
        """点赞角色"""
        # 检查是否已经点赞过
        existing = db.query(CharacterLike).filter(
            CharacterLike.character_id == character_id,
            CharacterLike.user_id == user_id
        ).first()

        if existing:
            raise Exception("你已经点过赞了")

        # 记录点赞
        like = CharacterLike(
            character_id=character_id,
            user_id=user_id,
            created_at=datetime.now()  # 🔥 改为普通 datetime，去掉 timezone.utc
        )
        db.add(like)

        # 更新点赞数
        character = db.query(Character).filter(Character.id == character_id).first()
        character.like_count += 1
        db.commit()
        db.refresh(character)

    @staticmethod
    def unlike_character(db: Session, character_id: int, user_id: int) -> bool:
        """
        取消点赞
        Returns:
            bool: 是否成功（False表示还没点赞）
        """
        # 查找点赞记录
        like = db.query(CharacterLike).filter(
            CharacterLike.character_id == character_id,
            CharacterLike.user_id == user_id
        ).first()

        if not like:
            return False

        # 删除点赞记录
        db.delete(like)

        # 更新角色的点赞数
        character = db.query(Character).filter(Character.id == character_id).first()
        if character and character.like_count > 0:
            character.like_count -= 1

        db.commit()
        return True

    @classmethod
    def get_character_like_status(cls, db, current_user, character_id):
        return CharacterLikeRepository.get_like_status(db, current_user.id, character_id)

    @classmethod
    def batch_get_like_status(cls, db, current_user, character_ids):
        # 查询当前用户对所有角色的点赞记录
        likes = CharacterLikeRepository.batch_get_like_status(db, current_user.id, character_ids)
        # 构建点赞状态映射
        liked_map = {like.character_id: True for like in likes}

        # 确保所有请求的 ID 都在返回结果中（未点赞的默认为 False）
        for char_id in character_ids:
            if char_id not in liked_map:
                liked_map[char_id] = False
        return liked_map


    # TODO 暂时还没用

    # @staticmethod
    # def calculate_popularity_score(db: Session, character_id: int) -> float:
    #     """计算热度得分（可用于排序）"""
    #     character = db.query(Character).filter(Character.id == character_id).first()
    #     if not character:
    #         return 0.0
    #
    #     # 各项指标的权重
    #     weights = {
    #         'usage_count': 0.3,
    #         'recent_usage_count': 0.4,
    #         'like_count': 0.2,
    #         'chat_count': 0.1
    #     }
    #
    #     # 归一化处理（根据最大值）
    #     max_stats = db.query(
    #         func.max(Character.usage_count).label('max_usage'),
    #         func.max(Character.recent_usage_count).label('max_recent'),
    #         func.max(Character.like_count).label('max_like'),
    #         func.max(Character.chat_count).label('max_chat')
    #     ).first()
    #
    #     score = 0
    #     if max_stats.max_usage > 0:
    #         score += weights['usage_count'] * (character.usage_count / max_stats.max_usage)
    #     if max_stats.max_recent > 0:
    #         score += weights['recent_usage_count'] * (character.recent_usage_count / max_stats.max_recent)
    #     if max_stats.max_like > 0:
    #         score += weights['like_count'] * (character.like_count / max_stats.max_like)
    #     if max_stats.max_chat > 0:
    #         score += weights['chat_count'] * (character.chat_count / max_stats.max_chat)
    #
    #     character.popularity_score = round(score, 2)
    #     db.commit()
    #
    #     return character.popularity_score
    #
    # @staticmethod
    # def batch_update_popularity(db: Session):
    #     """批量更新所有角色的热度得分（可定时任务调用）"""
    #     characters = db.query(Character).all()
    #     for character in characters:
    #         CharacterStatService.calculate_popularity_score(db, character.id)
    #     db.commit()


