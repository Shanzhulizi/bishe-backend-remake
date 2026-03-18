from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.character import Character, character_categories, character_tags
from app.models.tag import Tag
from app.schemas.character import CharacterCreate


class CharacterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, character_id: int) -> Optional[Character]:
        """根据ID获取角色"""
        return self.db.query(Character).filter(
            Character.id == character_id
        ).first()




    def get_by_id_with_relations(self, character_id: int) -> Optional[Character]:
        """获取角色并加载关联的类别和标签"""
        return self.db.query(Character) \
            .options(
            joinedload(Character.categories),
            joinedload(Character.tags)
        ) \
            .filter(Character.id == character_id) \
            .first()

    def get_by_name(self, name: str) -> Optional[Character]:
        """根据名称获取角色"""
        return self.db.query(Character).filter(
            Character.name == name
        ).first()

    def get_all(
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

        query = self.db.query(Character).filter(Character.is_active == is_active)

        # 按类别筛选
        if category_id:
            query = query.join(character_categories).filter(
                character_categories.c.category_id == category_id
            )

        # 按标签筛选
        if tag_id:
            query = query.join(character_tags).filter(
                character_tags.c.tag_id == tag_id
            )

        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    Character.name.ilike(f"%{keyword}%"),
                    Character.description.ilike(f"%{keyword}%")
                )
            )

        # 是否官方
        if is_official is not None:
            query = query.filter(Character.is_official == is_official)

        # 总数
        total = query.count()

        # 分页数据
        characters = query.options(
            joinedload(Character.categories),
            joinedload(Character.tags)
        ).order_by(
            Character.popularity_score.desc(),
            Character.created_at.desc()
        ).offset(skip).limit(limit).all()

        return characters, total

    def create_with_relations(self, data: CharacterCreate) -> Character:

        """创建角色"""

        """创建角色并添加关联"""
        # 1. 创建角色
        character = Character(
            name=data.name,
            description=data.description,
            worldview=data.worldview,
            avatar=data.avatar,
            voice_id=data.voice_id,
            greeting=data.greeting,
            is_official=data.is_official,
            is_active=True,
            usage_count=0,
            chat_count=0,
            like_count=0,
            recent_usage_count=0,
            popularity_score=0.0
        )
        self.db.add(character)
        self.db.flush()  # 获取 ID

        # 2. 添加类别
        if data.category_ids:
            categories = self.db.query(Category).filter(
                Category.id.in_(data.category_ids)
            ).all()
            character.categories = categories

        # 3. 添加标签
        if data.tag_ids:
            tags = self.db.query(Tag).filter(
                Tag.id.in_(data.tag_ids)
            ).all()
            character.tags = tags

        self.db.commit()
        self.db.refresh(character)
        return character

    def update_basic(self, character: Character, **kwargs) -> Character:
        """更新基本字段"""
        for key, value in kwargs.items():
            if value is not None:
                setattr(character, key, value)
        character.updated_at = datetime.now()
        self.db.add(character)
        self.db.flush()
        return character

    def update_categories(self, character: Character, category_ids: Optional[List[int]]) -> Character:
        """更新角色类别"""
        if category_ids is not None:
            if category_ids:  # 有传且不为空
                categories = self.db.query(Category).filter(
                    Category.id.in_(category_ids)
                ).all()
                character.categories = categories
            else:  # 传了空列表，清空所有类别
                character.categories = []
            self.db.add(character)
            self.db.flush()
        return character

    def update_tags(self, character: Character, tag_ids: Optional[List[int]]) -> Character:
        """更新角色标签"""
        if tag_ids is not None:
            if tag_ids:  # 有传且不为空
                tags = self.db.query(Tag).filter(
                    Tag.id.in_(tag_ids)
                ).all()
                character.tags = tags
            else:  # 传了空列表，清空所有标签
                character.tags = []
            self.db.add(character)
            self.db.flush()
        return character

    def update_complete(self, character_id: int, data: dict) -> Optional[Character]:
        """完整更新角色（一次性更新所有）"""
        character = self.get_by_id(character_id)
        if not character:
            return None

        # 1. 更新基本字段
        basic_fields = {
            'name': data.get('name'),
            'description': data.get('description'),
            'worldview': data.get('worldview'),
            'avatar': data.get('avatar'),
            'voice_id': data.get('voice_id'),
            'greeting': data.get('greeting'),
            'is_official': data.get('is_official'),
            'is_active': data.get('is_active')
        }
        character = self.update_basic(character, **basic_fields)

        # 2. 更新类别
        if 'category_ids' in data:
            character = self.update_categories(character, data['category_ids'])

        # 3. 更新标签
        if 'tag_ids' in data:
            character = self.update_tags(character, data['tag_ids'])

        return character

    def delete(self, character_id: int) -> bool:
        """删除角色（硬删除）"""
        character = self.get_by_id(character_id)
        if character:
            self.db.delete(character)
            self.db.flush()
            return True
        return False

    def soft_delete(self, character_id: int) -> bool:
        """软删除"""
        character = self.get_by_id(character_id)
        if character:
            character.is_active = False
            character.updated_at = datetime.now()
            self.db.add(character)
            self.db.flush()
            return True
        return False

    def increment_like_count(self, character_id: int):
        """增加点赞数"""
        self.db.query(Character).filter(Character.id == character_id).update({
            Character.like_count: Character.like_count + 1
        })
        self.db.flush()

    def decrement_like_count(self, character_id: int):
        """减少点赞数"""
        self.db.query(Character).filter(Character.id == character_id).update({
            Character.like_count: Character.like_count - 1
        })
        self.db.flush()

    #  ----------------------目前用到了这里，下面的还没有使用------------------------------------------



    def increment_chat_count(self, character_id: int):
        """增加聊天次数"""
        self.db.query(Character).filter(Character.id == character_id).update({
            Character.chat_count: Character.chat_count + 1,
            Character.recent_usage_count: Character.recent_usage_count + 1,
            Character.last_used_at: datetime.now()
        })
        self.db.flush()



    def update_popularity_score(self, character_id: int):
        """更新热度分数"""
        character = self.get_by_id(character_id)
        if character:
            score = (
                    character.chat_count * 0.3 +
                    character.like_count * 0.5 +
                    character.recent_usage_count * 0.2
            )
            character.popularity_score = score
            self.db.add(character)
            self.db.flush()

    def get_popular(self, limit: int = 10) -> List[Character]:
        """获取热门角色"""
        return self.db.query(Character).filter(
            Character.is_active == True
        ).order_by(
            Character.popularity_score.desc()
        ).limit(limit).all()

    def get_new(self, limit: int = 10) -> List[Character]:
        """获取最新角色"""
        return self.db.query(Character).filter(
            Character.is_active == True
        ).order_by(
            Character.created_at.desc()
        ).limit(limit).all()

    def count_by_category(self, category_id: int) -> int:
        """统计某个类别下的角色数量"""
        return self.db.query(character_categories).filter(
            character_categories.c.category_id == category_id
        ).count()

    def count_by_tag(self, tag_id: int) -> int:
        """统计某个标签下的角色数量"""
        return self.db.query(character_tags).filter(
            character_tags.c.tag_id == tag_id
        ).count()

    def get_like_count(self, character_id):
        "获取某角色点赞数"
        character = self.get_by_id(character_id)
        return character.like_count if character else 0