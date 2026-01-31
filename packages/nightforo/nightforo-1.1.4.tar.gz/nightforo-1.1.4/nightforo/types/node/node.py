from typing import Any, Dict, List, Optional

from pydantic import BaseModel

__all__ = ("Breadcrumb", "Node", "NodeCreateOrUpdate")


class Breadcrumb(BaseModel):
    node_id: Optional[int] = None
    title: Optional[str] = None
    node_type_id: Optional[str] = None


class Node(BaseModel):
    node_id: int

    title: Optional[str] = None
    node_name: Optional[str] = None
    node_type_id: Optional[str] = None
    breadcrumbs: Optional[List[Breadcrumb]] = None
    type_data: Optional[Dict[str, Any]] = None
    view_url: Optional[str] = None
    description: Optional[str] = None
    parent_node_id: Optional[int] = None
    display_order: Optional[int] = None
    display_in_list: Optional[bool] = None


class NodeCreateOrUpdate(BaseModel):
    title: str
    node_name: str
    description: str
    parent_node_id: int
    display_order: int
    display_in_list: bool
