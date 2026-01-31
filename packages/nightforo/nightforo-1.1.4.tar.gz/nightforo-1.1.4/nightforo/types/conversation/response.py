from typing import List, Optional

from pydantic import BaseModel

from ..conversation_message import ConversationMessage
from ..pagination import Pagination
from .conversation import Conversation

__all__ = (
    "ConversationCreateResponse",
    "ConversationDeleteResponse",
    "ConversationGetResponse",
    "ConversationInviteResponse",
    "ConversationMarkReadResponse",
    "ConversationMarkUnreadResponse",
    "ConversationMessagesGetResponse",
    "ConversationStarResponse",
    "ConversationUpdateResponse",
    "ConversationsGetResponse",
)


class ConversationsGetResponse(BaseModel):
    conversations: List[Conversation]
    pagination: Pagination


class ConversationCreateResponse(BaseModel):
    success: bool
    conversation: Conversation


class ConversationGetResponse(BaseModel):
    conversation: Conversation
    messages: Optional[List[ConversationMessage]] = None
    pagination: Optional[Pagination] = None


class ConversationUpdateResponse(BaseModel):
    success: bool
    conversation: Conversation


class ConversationDeleteResponse(BaseModel):
    success: bool


class ConversationInviteResponse(BaseModel):
    success: bool


class ConversationMarkReadResponse(BaseModel):
    success: bool


class ConversationMarkUnreadResponse(BaseModel):
    success: bool


class ConversationMessagesGetResponse(BaseModel):
    messages: List[ConversationMessage]
    pagination: Pagination


class ConversationStarResponse(BaseModel):
    success: bool
