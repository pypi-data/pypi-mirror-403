from typing import List, Optional

from pydantic import BaseModel

from ..node import Node
from ..pagination import Pagination
from ..thread import Thread

__all__ = (
    "ForumGetResponse",
    "ForumMarkReadResponse",
    "ForumThreadsGetResponse",
)


class ForumGetResponse(BaseModel):
    forum: Node
    threads: Optional[List[Thread]] = None
    pagination: Optional[Pagination] = None
    sticky: Optional[List[Thread]] = None


class ForumMarkReadResponse(BaseModel):
    success: bool


class ForumThreadsGetResponse(BaseModel):
    threads: List[Thread]
    pagination: Pagination
    sticky: Optional[List[Thread]] = None
