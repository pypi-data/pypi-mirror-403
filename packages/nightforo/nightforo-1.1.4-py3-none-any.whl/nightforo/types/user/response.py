from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from ...groups import ArzGuardGroupsIdsEnum, ArzGuardGroupsNamesEnum
from ..pagination import Pagination
from ..profile_post import ProfilePost
from .user import User

__all__ = (
    "DemoteUserResponse",
    "GetDemoteGroupsResponse",
    "GetPromoteGroupsResponse",
    "PromoteUserResponse",
    "UserAvatarDeleteResponse",
    "UserAvatarUpdateResponse",
    "UserCreateResponse",
    "UserDeleteResponse",
    "UserFindEmailResponse",
    "UserFindNameResponse",
    "UserGetResponse",
    "UserProfilePostsGetResponse",
    "UserUpdateResponse",
    "UsersGetResponse",
)


class UsersGetResponse(BaseModel):
    users: List[User]
    pagination: Pagination


class UserCreateResponse(BaseModel):
    success: bool
    user: User


class UserFindEmailResponse(BaseModel):
    user: Optional[User] = None


class UserFindNameResponse(BaseModel):
    exact: Optional[User] = None
    recommendations: List[User]


class UserGetResponse(BaseModel):
    user: User
    profile_posts: Optional[List[ProfilePost]] = None
    pagination: Optional[Pagination] = None


class UserUpdateResponse(BaseModel):
    success: bool
    user: User


class UserDeleteResponse(BaseModel):
    success: bool


class UserAvatarUpdateResponse(BaseModel):
    success: bool


class UserAvatarDeleteResponse(BaseModel):
    success: bool


class UserProfilePostsGetResponse(BaseModel):
    profile_posts: List[ProfilePost]
    pagination: Pagination


class GetDemoteGroupsResponse(BaseModel):
    success: Optional[bool] = None
    groups: Dict[ArzGuardGroupsIdsEnum, ArzGuardGroupsNamesEnum]


class GetPromoteGroupsResponse(BaseModel):
    success: Optional[bool] = None
    groups: Dict[ArzGuardGroupsIdsEnum, ArzGuardGroupsNamesEnum]


class PromoteUserResponse(BaseModel):
    success: bool
    groups: Union[
        Dict[ArzGuardGroupsIdsEnum, ArzGuardGroupsNamesEnum],
        List[ArzGuardGroupsNamesEnum],
    ]  # Если нет групп - пустой список, иначе dict
    user: Optional[User] = None


class DemoteUserResponse(BaseModel):
    success: bool
    groups: Union[
        Dict[ArzGuardGroupsIdsEnum, ArzGuardGroupsNamesEnum],
        List[ArzGuardGroupsNamesEnum],
    ]  # Если нет групп - пустой список, иначе dict
    user: Optional[User] = None
