from typing import List, Optional

from pydantic import BaseModel

__all__ = (
    "ConversationCreateParams",
    "ConversationDeleteParams",
    "ConversationGetMessagesParams",
    "ConversationGetParams",
    "ConversationInviteParams",
    "ConversationMarkReadParams",
    "ConversationStarParams",
    "ConversationUpdateParams",
    "ConversationsGetParams",
)


class ConversationsGetParams(BaseModel):
    page: Optional[int] = None
    starter_id: Optional[int] = None
    receiver_id: Optional[int] = None
    starred: Optional[bool] = None
    unread: Optional[bool] = None


class ConversationCreateParams(BaseModel):
    recipient_ids: List[int]
    title: str
    message: str
    attachment_key: Optional[str] = None
    conversation_open: Optional[bool] = None
    open_invite: Optional[bool] = None


class ConversationGetParams(BaseModel):
    with_messages: Optional[bool] = None
    page: Optional[int] = None


class ConversationUpdateParams(BaseModel):
    title: Optional[str] = None
    open_invite: Optional[bool] = None
    conversation_open: Optional[bool] = None


class ConversationDeleteParams(BaseModel):
    ignore: Optional[bool] = None


class ConversationInviteParams(BaseModel):
    recipient_ids: List[int]


class ConversationMarkReadParams(BaseModel):
    date: Optional[int] = None


class ConversationGetMessagesParams(BaseModel):
    page: Optional[int] = None


class ConversationStarParams(BaseModel):
    star: Optional[bool] = None
