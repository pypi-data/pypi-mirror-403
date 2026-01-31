from typing import List, Optional

from pydantic import BaseModel, ConfigDict

__all__ = (
    "AttachmentUploadParams",
    "AttachmentsCreateNewKeyParams",
    "AttachmentsGetParams",
)


class AttachmentsGetParams(BaseModel):
    key: str


class AttachmentUploadParams(BaseModel):
    key: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AttachmentsCreateNewKeyParams(BaseModel):
    type: str
    context: Optional[List[str]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
