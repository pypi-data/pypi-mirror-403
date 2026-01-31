from pydantic import BaseModel

from ..user import User

__all__ = ("UserAlert",)


class UserAlert(BaseModel):
    action: str
    alert_id: int
    alert_text: str
    alert_url: str
    alerted_user_id: int
    auto_read: bool
    content_id: int
    content_type: str
    event_date: int
    read_date: int
    User: User
    user_id: int
    username: str
    view_date: int
