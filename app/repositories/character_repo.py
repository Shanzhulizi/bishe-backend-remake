from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.character import Character
from app.models.character_configs import CharacterConfigs


class CharacterRepository:

    def create_character(self, db: Session,

                         *,
                         name: str,
                         avatar: Optional[str],
                         description: Optional[str],
                         worldview: Optional[str],
                         persona: dict,
                         voice_code: Optional[str]
                         ):
        # 创建角色基本信息
        char = Character(
            name=name,
            avatar=avatar,
            description=description,
            worldview=worldview,
            voice_code=voice_code
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
