from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from ..user import Option, Privacy, Profile

__all__ = (
    "MeEmailUpdateParams",
    "MePasswordUpdateParams",
    "MeUpdateParams",
)


class MeUpdateParams(BaseModel):
    option: Optional[Option] = None
    profile: Optional[Profile] = None
    privacy: Optional[Privacy] = None
    visible: Optional[bool] = None
    activity_visible: Optional[bool] = None
    timezone: Optional[str] = None
    custom_title: Optional[str] = None
    custom_fields: Optional[Dict[str, str]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MeEmailUpdateParams(BaseModel):
    current_password: str
    email: str


class MePasswordUpdateParams(BaseModel):
    current_password: str
    new_password: str
