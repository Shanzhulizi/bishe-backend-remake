from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import select, update, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.character import Character
from app.schemas.character import CharacterCreate


class CharacterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, character_id: int) -> Optional[Character]:
        """根据ID获取角色"""

        stmt = select(Character).where(Character.id == character_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(self, character_id: int) -> Optional[Character]:
        """获取角色并加载关联的类别和标签"""
        stmt = select(Character).options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        ).where(Character.id == character_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Character]:
        """根据名称获取角色"""
        stmt = select(Character).where(Character.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
            self,
            skip: int = 0,
            limit: int = 20,
            category_id: Optional[int] = None,
            tag_id: Optional[int] = None,
            keyword: Optional[str] = None,
            is_official: Optional[bool] = None,
            is_active: bool = True
    ) -> Tuple[List[Character], int]:
        """获取角色列表（支持过滤和搜索）"""
        from app.models.character import character_categories, character_tags

        stmt = select(Character).where(Character.is_active == is_active)

        if category_id:
            stmt = stmt.join(character_categories).where(
                character_categories.c.category_id == category_id
            )

        if tag_id:
            stmt = stmt.join(character_tags).where(
                character_tags.c.tag_id == tag_id
            )

        if keyword:
            stmt = stmt.where(
                or_(
                    Character.name.ilike(f"%{keyword}%"),
                    Character.description.ilike(f"%{keyword}%")
                )
            )

        if is_official is not None:
            stmt = stmt.where(Character.is_official == is_official)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()

        # 分页数据
        stmt = stmt.options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        ).order_by(
            Character.popularity_score.desc(),
            Character.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        characters = result.scalars().all()

        return characters, total

    async def create_with_relations(self, data: CharacterCreate) -> Character:
        """创建角色并添加关联"""
        from app.models.category import Category
        from app.models.tag import Tag

        character = Character(
            name=data.name,
            description=data.description,
            worldview=data.worldview,
            avatar=data.avatar,
            voice_id=data.voice_id,
            greeting=data.greeting,
            is_official=data.is_official,
            is_active=True,
            view_count=0,
            chat_count=0,
            like_count=0,
            popularity_score=0.0
        )
        self.db.add(character)
        await self.db.flush()

        if data.category_ids:
            stmt = select(Category).where(Category.id.in_(data.category_ids))
            result = await self.db.execute(stmt)
            categories = result.scalars().all()
            character.categories = categories

        if data.tag_ids:
            stmt = select(Tag).where(Tag.id.in_(data.tag_ids))
            result = await self.db.execute(stmt)
            tags = result.scalars().all()
            character.tags = tags

        await self.db.commit()
        await self.db.refresh(character)
        return character

    async def update_basic(self, character: Character, **kwargs) -> Character:
        """更新基本字段"""
        for key, value in kwargs.items():
            if value is not None:
                setattr(character, key, value)
        character.updated_at = datetime.now()
        self.db.add(character)
        await self.db.flush()
        return character

    async def update_categories(self, character: Character, category_ids: Optional[List[int]]) -> Character:
        """更新角色类别"""
        from app.models.category import Category

        if category_ids is not None:
            if category_ids:
                stmt = select(Category).where(Category.id.in_(category_ids))
                result = await self.db.execute(stmt)
                categories = result.scalars().all()
                character.categories = categories
            else:
                character.categories = []
            self.db.add(character)
            await self.db.flush()
        return character

    async def update_tags(self, character: Character, tag_ids: Optional[List[int]]) -> Character:
        """更新角色标签"""
        from app.models.tag import Tag

        if tag_ids is not None:
            if tag_ids:
                stmt = select(Tag).where(Tag.id.in_(tag_ids))
                result = await self.db.execute(stmt)
                tags = result.scalars().all()
                character.tags = tags
            else:
                character.tags = []
            self.db.add(character)
            await self.db.flush()
        return character

    async def update_complete(self, character_id: int, data: dict) -> Optional[Character]:
        """完整更新角色"""
        character = await self.get_by_id(character_id)
        if not character:
            return None

        basic_fields = {
            'name': data.get('name'),
            'description': data.get('description'),
            'worldview': data.get('worldview'),
            'avatar': data.get('avatar'),
            'voice_id': data.get('voice_id'),
            'greeting': data.get('greeting'),
            'is_official': data.get('is_official'),
            'is_active': data.get('is_active'),
            'last_used_at': data.get('last_used_at')
        }
        character = await self.update_basic(character, **basic_fields)

        if 'category_ids' in data:
            character = await self.update_categories(character, data['category_ids'])

        if 'tag_ids' in data:
            character = await self.update_tags(character, data['tag_ids'])

        return character

    async def delete(self, character_id: int) -> bool:
        """删除角色（硬删除）"""
        character = await self.get_by_id(character_id)
        if character:
            await self.db.delete(character)
            await self.db.flush()
            return True
        return False

    async def soft_delete(self, character_id: int) -> bool:
        """软删除"""
        character = await self.get_by_id(character_id)
        if character:
            character.is_active = False
            character.updated_at = datetime.now()
            self.db.add(character)
            await self.db.flush()
            return True
        return False

    async def increment_like_count(self, character_id: int):
        """增加点赞数"""
        stmt = update(Character).where(Character.id == character_id).values(
            like_count=Character.like_count + 1
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def decrement_like_count(self, character_id: int):
        """减少点赞数"""
        stmt = update(Character).where(Character.id == character_id).values(
            like_count=Character.like_count - 1
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_like_count(self, character_id: int) -> int:
        """获取某角色点赞数"""
        character = await self.get_by_id(character_id)
        return character.like_count if character else 0

    async def get_chat_count(self, character_id: int) -> int:
        """获取角色的聊天数"""
        character = await self.get_by_id(character_id)
        return character.chat_count if character else 0

    async def increment_view_count(self, character_id: int):
        """增加浏览次数"""
        stmt = update(Character).where(Character.id == character_id).values(
            view_count=Character.view_count + 1
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def increment_chat_count(self, character_id: int):
        """增加聊天次数"""
        stmt = update(Character).where(Character.id == character_id).values(
            chat_count=Character.chat_count + 1
        )
        await self.db.execute(stmt)
        await self.db.flush()
