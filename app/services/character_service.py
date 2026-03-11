from fastapi import HTTPException
from openai.types.beta.realtime import Session
from starlette import status

from app.core.logging import get_logger
from app.persona.builder import PersonaBuilder
from app.repositories.character_repo import CharacterRepository
from app.schemas.character import CharacterCreate

logger= get_logger(__name__)
class CharacterService:
    def __init__(self, repo: CharacterRepository):
        self.repo = repo

    def create_character(self, db: Session, data: CharacterCreate):
        persona = PersonaBuilder.apply_tags(data.tags)

        logger.info(f"voice_code:{data.voice_code}")
        return self.repo.create_character(
            db,
            name=data.name,
            avatar=data.avatar,
            description=data.description,
            worldview=data.worldview,
            persona=persona,
            voice_code=data.voice_code
        )

    def get_character_by_id(self, db, character_id):
        char = self.repo.get_basic_by_id(db, character_id)
        if not char:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return char

    def get_all_characters_basic(self, db: Session):
        return self.repo.get_all_basic(db)
