from typing import Optional

from pydantic import BaseModel

__all__ = ("AuthFromSessionParams", "AuthLoginTokenParams", "AuthTestParams")


class AuthFromSessionParams(BaseModel):
    session_id: Optional[str] = None
    remember_cookie: Optional[str] = None


class AuthLoginTokenParams(BaseModel):
    user_id: int
    limit_ip: Optional[str] = None
    return_url: Optional[str] = None
    force: Optional[bool] = None
    remember: Optional[bool] = None


class AuthTestParams(BaseModel):
    login: str
    password: str
    limit_ip: Optional[str] = None
