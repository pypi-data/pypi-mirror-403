from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

from ..attachment import Attachment
from ..user import User

if TYPE_CHECKING:
    from ..thread import Thread

__all__ = ("Post",)


class Post(BaseModel):
    post_id: int
    thread_id: int
    user_id: int
    username: str
    message: str
    user: User | None = Field(alias="User", default=None)

    is_first_post: Optional[bool] = None
    is_last_post: Optional[bool] = None
    is_unread: Optional[bool] = None
    message_parsed: Optional[str] = None
    can_edit: Optional[bool] = None
    can_soft_delete: Optional[bool] = None
    can_hard_delete: Optional[bool] = None
    can_react: Optional[bool] = None
    can_view_attachments: Optional[bool] = None
    view_url: Optional[str] = None
    Thread: Optional[Thread] = None
    Attachments: Optional[List[Attachment]] = None
    is_reacted_to: Optional[bool] = None
    visitor_reaction_id: Optional[int] = None
    vote_score: Optional[int] = None
    can_content_vote: Optional[bool] = None
    allowed_content_vote_types: Optional[List[str]] = None
    is_content_voted: Optional[bool] = None
    visitor_content_vote: Optional[str] = None
    post_date: Optional[int] = None
    message_state: Optional[str] = None
    attach_count: Optional[int] = None
    warning_message: Optional[str] = None
    position: Optional[int] = None
    last_edit_date: Optional[int] = None
    reaction_score: Optional[int] = None
