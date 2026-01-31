from typing import Any, Dict, Optional

from pydantic import BaseModel

from .node import NodeCreateOrUpdate

__all__ = ("NodeCreateParams", "NodeDeleteParams", "NodeUpdateParams")


class NodeCreateParams(BaseModel):
    node: NodeCreateOrUpdate
    type_data: Dict[str, Any]
    node_type_id: str


class NodeUpdateParams(BaseModel):
    node: NodeCreateOrUpdate
    type_data: Dict[str, Any]


class NodeDeleteParams(BaseModel):
    delete_children: Optional[bool] = None
