from typing import Optional

from pydantic import BaseModel

__all__ = (
    "AlertMarkParams",
    "AlertSendParams",
    "AlertsGetParams",
    "AlertsMarkAllParams",
)


class AlertsGetParams(BaseModel):
    page: Optional[int] = None
    cutoff: Optional[int] = None
    unviewed: Optional[bool] = None
    unread: Optional[bool] = None


class AlertSendParams(BaseModel):
    to_user_id: int
    alert: str
    from_user_id: Optional[int] = None
    link_url: Optional[str] = None
    link_title: Optional[str] = None


class AlertsMarkAllParams(BaseModel):
    read: Optional[bool] = None
    viewed: Optional[bool] = None


class AlertMarkParams(BaseModel):
    read: Optional[bool] = None
    unread: Optional[bool] = None
    viewed: Optional[bool] = None
