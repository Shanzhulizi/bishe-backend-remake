from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.character import Character
from app.models.character_configs import CharacterConfigs
from app.models.character_usage import CharacterLike


class CharacterLikeRepository:

    def create_character(self, db: Session,

                         *,
                         name: str,
                         avatar: Optional[str],
                         description: Optional[str],
                         worldview: Optional[str],
                         persona: dict
                         ):
        # 创建角色基本信息
        char = Character(
            name=name,
            avatar=avatar,
            description=description,
            worldview=worldview
        )
        db.add(char)
        db.flush()  # 拿到 char.id

        # 创建角色配置
        config = CharacterConfigs(
            character_id=char.id,
            persona=persona
        )
        db.add(config)

        db.commit()
        db.refresh(char)
        return char

    # 不确定是否可用
    @staticmethod
    def get_by_id(db: Session, character_id: int) -> Character | None:
        return (
            db.query(Character)
                .options(joinedload(Character.config))  # 一次性加载 persona
                .filter(Character.id == character_id)
                .first()
        )

    def get_basic_by_id(self, db: Session, character_id: int) -> Character | None:
        return db.query(Character).filter(Character.id == character_id).first()

    # 获取所有角色的基本信息
    def get_all_basic(self, db: Session):
        return db.query(
            Character.id,
            Character.name,
            Character.avatar,
            Character.description,
            Character.like_count
        ).all()

    @classmethod
    def get_like_status(cls, db, id, character_id):

        is_liked = db.query(CharacterLike).filter(
            CharacterLike.character_id == character_id,
            CharacterLike.user_id == id
        ).first() is not None
        return is_liked

    @classmethod
    def batch_get_like_status(cls, db, id, character_ids):
        likes = db.query(CharacterLike).filter(
            CharacterLike.character_id.in_(character_ids),
            CharacterLike.user_id == id
        ).all()
        return likes