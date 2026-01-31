from typing import Any, List

from pydantic import BaseModel

from .node import Node

__all__ = (
    "NodeCreateResponse",
    "NodeDeleteResponse",
    "NodeGetResponse",
    "NodeUpdateResponse",
    "NodesFlattenedGetResponse",
    "NodesGetResponse",
)


class NodesGetResponse(BaseModel):
    tree_map: List[Any]
    nodes: List[Node]


class NodeCreateResponse(BaseModel):
    node: Node


class NodesFlattenedGetResponse(BaseModel):
    nodes_flat: List[Any]


class NodeGetResponse(BaseModel):
    node: Node


class NodeUpdateResponse(BaseModel):
    node: Node


class NodeDeleteResponse(BaseModel):
    success: bool
