from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from ..vote_type import VoteTypeEnum

__all__ = (
    "ThreadChangeTypeParams",
    "ThreadCreateParams",
    "ThreadDeleteParams",
    "ThreadGetParams",
    "ThreadMarkReadParams",
    "ThreadMoveParams",
    "ThreadPostsGetParams",
    "ThreadUpdateParams",
    "ThreadVoteParams",
    "ThreadsGetParams",
)


class ThreadsGetParams(BaseModel):
    page: Optional[int] = None
    prefix_id: Optional[int] = None
    starter_id: Optional[int] = None
    last_days: Optional[int] = None
    unread: Optional[bool] = None
    thread_type: Optional[str] = None
    order: Optional[str] = None
    direction: Optional[str] = None


class ThreadCreateParams(BaseModel):
    node_id: int
    title: str
    message: str
    discussion_type: Optional[str] = None
    prefix_id: Optional[int] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    discussion_open: Optional[bool] = None
    sticky: Optional[bool] = None
    attachment_key: Optional[str] = None


class ThreadGetParams(BaseModel):
    with_posts: Optional[bool] = None
    page: Optional[int] = None
    with_first_post: Optional[bool] = None
    with_last_post: Optional[bool] = None
    order: Optional[str] = None


class ThreadUpdateParams(BaseModel):
    prefix_id: Optional[int] = None
    title: Optional[str] = None
    discussion_open: Optional[bool] = None
    sticky: Optional[bool] = None
    custom_fields: Optional[Dict[str, str]] = None
    add_tags: Optional[List[str]] = None
    remove_tags: Optional[List[str]] = None


class ThreadDeleteParams(BaseModel):
    hard_delete: Optional[bool] = None
    reason: Optional[str] = None
    starter_alert: Optional[bool] = None
    starter_alert_reason: Optional[str] = None


class ThreadChangeTypeParams(BaseModel):
    new_thread_type_id: str


class ThreadMarkReadParams(BaseModel):
    date: Optional[int] = None


class ThreadMoveParams(BaseModel):
    target_node_id: int
    prefix_id: Optional[int] = None
    title: Optional[str] = None
    notify_watchers: Optional[bool] = None
    starter_alert: Optional[bool] = None
    starter_alert_reason: Optional[str] = None


class ThreadPostsGetParams(BaseModel):
    page: Optional[int] = None
    order: Optional[str] = None


class ThreadVoteParams(BaseModel):
    type: VoteTypeEnum
