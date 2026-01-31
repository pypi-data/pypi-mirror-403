from pydantic import BaseModel

__all__ = ("Page",)


class Page(BaseModel):
    publish_date: int
    view_count: int
