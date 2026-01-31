from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ..user import User
from ..vote_type import VoteTypeEnum

if TYPE_CHECKING:
    from ..node import Node

__all__ = ("Thread",)


class Thread(BaseModel):
    thread_id: int
    node_id: int
    title: str
    username: str
    user_id: int
    user: User | None = Field(alias="User", default=None)
    is_watching: bool | None = None
    visitor_post_count: int | None = None
    is_unread: bool | None = None
    custom_fields: dict[str, Any] | None = None
    tags: list[str] | None = None
    prefix: str | None = None
    can_edit: bool | None = None
    can_edit_tags: bool | None = None
    can_reply: bool | None = None
    can_soft_delete: bool | None = None
    can_hard_delete: bool | None = None
    can_view_attachments: bool | None = None
    view_url: str | None = None
    is_first_post_pinned: bool | None = None
    highlighted_post_ids: list[int] | None = None
    is_search_engine_indexable: bool | None = None
    index_state: str | None = None
    Forum: Node | None = None
    vote_score: int | None = None
    can_content_vote: bool | None = None
    allowed_content_vote_types: list[str] | None = None
    is_content_voted: bool | None = None
    visitor_content_vote: VoteTypeEnum | None = None
    reply_count: int | None = None
    view_count: int | None = None
    post_date: int | None = None
    sticky: bool | None = None
    discussion_state: str | None = None
    discussion_open: bool | None = None
    discussion_type: str | None = None
    first_post_id: int | None = None
    last_post_date: int | None = None
    last_post_id: int | None = None
    last_post_user_id: int | None = None
    last_post_username: str | None = None
    first_post_reaction_score: int | None = None
    prefix_id: int | None = None
