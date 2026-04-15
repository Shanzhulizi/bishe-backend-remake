from pydantic import BaseModel


class  CreateConversationRequest(BaseModel):
    character_id: int
    greeting: str