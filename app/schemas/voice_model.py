# app/schemas/voice_model.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VoiceModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    language: str = "zh"


class VoiceModelCreate(VoiceModelBase):
    pass


class VoiceModelResponse(VoiceModelBase):
    id: int
    model_code: str
    preview_url: Optional[str] = None
    duration: float
    use_count: int
    created_at: datetime

    class Config:
        from_attributes = True