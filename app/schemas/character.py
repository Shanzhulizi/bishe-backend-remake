from typing import Optional

from pydantic import BaseModel, Field


class DialogueStyle(BaseModel):
    directness: float = Field(ge=0, le=1)
    verbosity: float = Field(ge=0, le=1)
    emotional_expressiveness: float = Field(ge=0, le=1)
    guidance_style: float = Field(ge=0, le=1)
    dialog_control: float = Field(ge=0, le=1)
    tolerance: float = Field(ge=0, le=1)


class Traits(BaseModel):
    bravery: float = Field(ge=0, le=1)
    kindness: float = Field(ge=0, le=1)
    logic: float = Field(ge=0, le=1)
    emotionality: float = Field(ge=0, le=1)
    curiosity: float = Field(ge=0, le=1)
    discipline: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    flexibility: float = Field(ge=0, le=1)


class MemoryStrategy(BaseModel):
    short_term_memory: int = Field(ge=1, le=20)
    long_term_memory: int = Field(ge=10, le=200)


class Persona(BaseModel):
    traits: Traits
    dialogue_style: DialogueStyle
    memory_strategy: MemoryStrategy


class CharacterCreate(BaseModel):
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    worldview: Optional[str] = None
    # voice: string
    tags: list[str] = []
    voice_code: Optional[str] = None  # 新增

class CharacterResponse(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    worldview: Optional[str] = None
    is_active: bool = True
    persona: Optional[Persona] = None  # 对应 CharacterConfigs.persona

    voice_code: Optional[str]= None  # 新增
    class Config:
        from_attributes = True




class CharacterListItem(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    # worldview: Optional[str] = None
    # tags: List[str] = []
    like_count: int = 0
    # is_liked: bool = False
    usage_count: int = 0
    chat_count: int = 0
    popularity_score: float = 0.0  # 热度得分
    recent_usage: int = 0  # 近期使用数
    # recent_likes: int = 0  # 近期点赞数    # 数据库没有这一项
    # hot_level: int = 0  # 热度等级 1-5

    class Config:
        from_attributes = True








