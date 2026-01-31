from pydantic import BaseModel

from .conversation_message import ConversationMessage

__all__ = (
    "ConversationMessageGetResponse",
    "ConversationMessageReactResponse",
    "ConversationMessageReplyResponse",
    "ConversationMessageUpdateResponse",
)


class ConversationMessageReplyResponse(BaseModel):
    success: bool
    message: ConversationMessage


class ConversationMessageUpdateResponse(BaseModel):
    success: bool
    message: ConversationMessage


class ConversationMessageReactResponse(BaseModel):
    success: bool
    action: str


class ConversationMessageGetResponse(BaseModel):
    message: ConversationMessage
