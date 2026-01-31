from typing import Optional

from pydantic import BaseModel

__all__ = (
    "ProfilePostCommentCreateParams",
    "ProfilePostCommentDeleteParams",
    "ProfilePostCommentReactParams",
    "ProfilePostCommentUpdateParams",
    "ProfilePostCommentsGetParams",
)


class ProfilePostCommentCreateParams(BaseModel):
    profile_post_id: int
    message: str
    attachment_key: Optional[str] = None


class ProfilePostCommentUpdateParams(BaseModel):
    message: str
    author_alert: Optional[bool] = None
    author_alert_reason: Optional[str] = None
    attachment_key: Optional[str] = None


class ProfilePostCommentDeleteParams(BaseModel):
    hard_delete: Optional[bool] = None
    reason: Optional[str] = None
    author_alert: Optional[bool] = None
    author_alert_reason: Optional[str] = None


class ProfilePostCommentReactParams(BaseModel):
    reaction_id: int


class ProfilePostCommentsGetParams(BaseModel):
    page: Optional[int] = None
    direction: Optional[str] = None
