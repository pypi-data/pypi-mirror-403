from typing import Dict, Optional

from pydantic import BaseModel

from ...api_scopes import APIScopeIdsEnum

__all__ = ("ApiKey", "IndexGetResponse")


class ApiKey(BaseModel):
    type: str
    user_id: Optional[int] = None
    allow_all_scopes: bool
    scopes: Dict[APIScopeIdsEnum, bool]


class IndexGetResponse(BaseModel):
    version_id: int
    site_title: str
    base_url: str
    api_url: str
    key: ApiKey
