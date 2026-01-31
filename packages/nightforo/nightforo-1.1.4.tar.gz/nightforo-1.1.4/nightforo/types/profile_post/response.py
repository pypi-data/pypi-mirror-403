from typing import List, Optional

from pydantic import BaseModel

from ..pagination import Pagination
from ..profile_post_comment import ProfilePostComment
from .profile_post import ProfilePost

__all__ = (
    "ProfilePostCommentsGetResponse",
    "ProfilePostCreateResponse",
    "ProfilePostDeleteResponse",
    "ProfilePostGetResponse",
    "ProfilePostReactResponse",
    "ProfilePostUpdateResponse",
)


class ProfilePostCreateResponse(BaseModel):
    success: bool
    profile_post: ProfilePost


class ProfilePostGetResponse(BaseModel):
    profile_post: ProfilePost
    comments: Optional[List[ProfilePostComment]] = None
    pagination: Optional[Pagination] = None


class ProfilePostUpdateResponse(BaseModel):
    success: bool
    profile_post: ProfilePost


class ProfilePostDeleteResponse(BaseModel):
    success: bool


class ProfilePostCommentsGetResponse(BaseModel):
    comments: List[ProfilePostComment]
    pagination: Pagination


class ProfilePostReactResponse(BaseModel):
    success: bool
    action: str
