from typing import Optional

from pydantic import BaseModel

__all__ = ("ForumGetParams", "ForumMarkReadParams", "ForumThreadsGetParams")


class ForumGetParams(BaseModel):
    with_threads: Optional[bool] = None
    page: Optional[int] = None
    prefix_id: Optional[int] = None
    starter_id: Optional[int] = None
    last_days: Optional[int] = None
    unread: Optional[bool] = None
    thread_type: Optional[str] = None
    order: Optional[str] = None
    direction: Optional[str] = None


class ForumMarkReadParams(BaseModel):
    date: Optional[int] = None


class ForumThreadsGetParams(BaseModel):
    page: Optional[int] = None
    prefix_id: Optional[int] = None
    starter_id: Optional[int] = None
    last_days: Optional[int] = None
    unread: Optional[bool] = None
    thread_type: Optional[str] = None
    order: Optional[str] = None
    direction: Optional[str] = None
