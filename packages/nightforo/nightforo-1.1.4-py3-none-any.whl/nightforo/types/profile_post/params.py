from typing import Optional

from pydantic import BaseModel

__all__ = (
    "ProfilePostCreateParams",
    "ProfilePostDeleteParams",
    "ProfilePostGetParams",
    "ProfilePostReactParams",
    "ProfilePostUpdateParams",
)


class ProfilePostCreateParams(BaseModel):
    user_id: int
    message: str
    attachment_key: Optional[str] = None


class ProfilePostGetParams(BaseModel):
    with_comments: Optional[bool] = None
    page: Optional[int] = None
    direction: Optional[str] = None


class ProfilePostUpdateParams(BaseModel):
    message: str
    author_alert: Optional[bool] = None
    author_alert_reason: Optional[str] = None
    attachment_key: Optional[str] = None


class ProfilePostDeleteParams(BaseModel):
    hard_delete: Optional[bool] = None
    reason: Optional[str] = None
    author_alert: Optional[bool] = None
    author_alert_reason: Optional[str] = None


class ProfilePostReactParams(BaseModel):
    reaction_id: int
