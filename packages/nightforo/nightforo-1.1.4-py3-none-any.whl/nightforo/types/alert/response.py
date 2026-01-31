from typing import List

from pydantic import BaseModel

from ..pagination import Pagination
from .alert import UserAlert

__all__ = (
    "AlertGetResponse",
    "AlertMarkResponse",
    "AlertSendResponse",
    "AlertsGetResponse",
    "AlertsMarkAllResponse",
)


class AlertsGetResponse(BaseModel):
    alerts: List[UserAlert]
    pagination: Pagination


class AlertSendResponse(BaseModel):
    success: bool


class AlertsMarkAllResponse(BaseModel):
    success: bool


class AlertGetResponse(BaseModel):
    alert: UserAlert


class AlertMarkResponse(BaseModel):
    success: bool
