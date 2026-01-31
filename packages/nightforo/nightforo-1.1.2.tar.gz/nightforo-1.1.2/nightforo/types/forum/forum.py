from pydantic import BaseModel

__all__ = ("Forum",)


class Forum(BaseModel):
    forum_type_id: str
    allow_posting: bool
    require_prefix: bool
    min_tags: int
