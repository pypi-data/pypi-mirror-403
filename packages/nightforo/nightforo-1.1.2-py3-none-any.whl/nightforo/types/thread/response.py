from typing import List, Optional

from pydantic import BaseModel

from ..pagination import Pagination
from ..post import Post
from .thread import Thread

__all__ = (
    "ThreadChangeTypeResponse",
    "ThreadCreateResponse",
    "ThreadDeleteResponse",
    "ThreadGetResponse",
    "ThreadMarkReadResponse",
    "ThreadMoveResponse",
    "ThreadPostsGetResponse",
    "ThreadUpdateResponse",
    "ThreadVoteResponse",
    "ThreadsGetResponse",
)


class ThreadsGetResponse(BaseModel):
    threads: List[Thread]
    pagination: Pagination


class ThreadGetResponse(BaseModel):
    thread: Thread
    first_unread: Optional[Post] = None
    first_post: Optional[Post] = None
    last_post: Optional[Post] = None
    pinned_post: Optional[Post] = None
    highlighted_posts: Optional[List[Post]] = None
    posts: Optional[List[Post]] = None
    pagination: Optional[Pagination] = None


class ThreadCreateResponse(BaseModel):
    success: bool
    thread: Thread


class ThreadUpdateResponse(BaseModel):
    success: bool
    thread: Thread


class ThreadDeleteResponse(BaseModel):
    success: bool


class ThreadChangeTypeResponse(BaseModel):
    success: bool
    thread: Thread


class ThreadMarkReadResponse(BaseModel):
    success: bool


class ThreadMoveResponse(BaseModel):
    success: bool
    thread: Thread


class ThreadPostsGetResponse(BaseModel):
    pinned_post: Optional[Post] = None
    highlighted_posts: Optional[List[Post]] = None
    posts: List[Post]
    pagination: Pagination


class ThreadVoteResponse(BaseModel):
    success: bool
    action: str
