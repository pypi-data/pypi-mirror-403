from pydantic import BaseModel

__all__ = ("Pagination",)


class Pagination(BaseModel):
    current_page: int
    last_page: int
    per_page: int
    shown: int
    total: int
