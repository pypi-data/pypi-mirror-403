from typing import Optional

from pydantic import BaseModel

__all__ = (
    "ConversationMessageReactParams",
    "ConversationMessageReplyParams",
    "ConversationMessageUpdateParams",
)


class ConversationMessageReplyParams(BaseModel):
    conversation_id: int
    message: str
    attachment_key: Optional[str] = None


class ConversationMessageUpdateParams(BaseModel):
    message: str
    attachment_key: Optional[str] = None


class ConversationMessageReactParams(BaseModel):
    reaction_id: int
