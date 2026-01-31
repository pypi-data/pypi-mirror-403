from pydantic import BaseModel

__all__ = ("LatestUser", "Online", "Totals")


class Totals(BaseModel):
    thread: int
    messages: int
    users: int


class LatestUser(BaseModel):
    user_id: int
    username: str
    register_date: int


class Online(BaseModel):
    total: int
    members: int
    guests: int
