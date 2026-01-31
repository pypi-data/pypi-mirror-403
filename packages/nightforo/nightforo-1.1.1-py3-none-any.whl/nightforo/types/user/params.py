from typing import Dict, List, Optional

from pydantic import BaseModel

from ...groups import ArzGuardGroupsIdsEnum
from .user import DateOfBirth, Option, Privacy, Profile

__all__ = (
    "UserCreateParams",
    "UserDemoteParams",
    "UserGetParams",
    "UserProfilePostsGetParams",
    "UserPromoteParams",
    "UserRenameParams",
    "UserUpdateParams",
    "UsersFindEmailParams",
    "UsersFindNameParams",
    "UsersGetParams",
)


class UsersGetParams(BaseModel):
    page: Optional[int] = None


class UserCreateParams(BaseModel):
    username: str
    email: str
    password: str
    option: Optional[Option] = None
    profile: Optional[Profile] = None
    privacy: Optional[Privacy] = None
    visible: Optional[bool] = None
    activity_visible: Optional[bool] = None
    timezone: Optional[str] = None
    custom_title: Optional[str] = None
    user_group_id: Optional[int] = None
    secondary_group_ids: Optional[List[int]] = None
    user_state: Optional[str] = None
    is_staff: Optional[bool] = None
    message_count: Optional[int] = None
    reaction_score: Optional[int] = None
    trophy_points: Optional[int] = None
    username_change_visible: Optional[bool] = None
    dob: Optional[Dict[str, int]] = None
    custom_fields: Optional[str] = None


class UsersFindEmailParams(BaseModel):
    email: str


class UsersFindNameParams(BaseModel):
    username: str


class UserGetParams(BaseModel):
    with_posts: Optional[bool] = None
    page: Optional[int] = None


class UserUpdateParams(BaseModel):
    option: Optional[Option] = None
    profile: Optional[Profile] = None
    privacy: Optional[Privacy] = None
    visible: Optional[bool] = None
    activity_visible: Optional[bool] = None
    timezone: Optional[str] = None
    custom_title: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    user_group_id: Optional[int] = None
    secondary_group_ids: Optional[List[int]] = None
    user_state: Optional[str] = None
    is_staff: Optional[bool] = None
    message_count: Optional[int] = None
    reaction_score: Optional[int] = None
    trophy_points: Optional[int] = None
    username_change_visible: Optional[bool] = None
    dob: Optional[DateOfBirth] = None
    custom_fields: Optional[str] = None


class UserRenameParams(BaseModel):
    rename_to: Optional[str] = None


class UserProfilePostsGetParams(BaseModel):
    page: int


class UserDemoteParams(BaseModel):
    group: ArzGuardGroupsIdsEnum


class UserPromoteParams(BaseModel):
    group: ArzGuardGroupsIdsEnum
