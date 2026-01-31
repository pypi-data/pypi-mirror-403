from typing import Optional

from pydantic import BaseModel

from ..vote_type import VoteTypeEnum

__all__ = (
    "PostCreateParams",
    "PostDeleteParams",
    "PostReactParams",
    "PostUpdateParams",
    "PostVoteParams",
)


class PostCreateParams(BaseModel):
    thread_id: int
    message: str
    attachment_key: Optional[str] = None


class PostUpdateParams(BaseModel):
    message: str
    silent: Optional[bool] = None
    clear_edit: Optional[bool] = None
    author_alert: Optional[bool] = None
    author_alert_reason: Optional[str] = None
    attachment_key: Optional[str] = None


class PostDeleteParams(BaseModel):
    hard_delete: Optional[bool] = None
    reason: Optional[str] = None
    author_alert: Optional[bool] = None
    author_alert_reason: Optional[str] = None


class PostReactParams(BaseModel):
    reaction_id: int


class PostVoteParams(BaseModel):
    type: VoteTypeEnum
