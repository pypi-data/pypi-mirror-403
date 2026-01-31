from pydantic import BaseModel

__all__ = ("Attachment",)


class Attachment(BaseModel):
    filename: str
    file_size: int
    height: int
    width: int
    thumbnail_url: str
    direct_url: str
    is_video: bool
    is_audio: bool
    attachment_id: int
    content_type: str
    content_id: int
    attach_date: int
    view_count: int
