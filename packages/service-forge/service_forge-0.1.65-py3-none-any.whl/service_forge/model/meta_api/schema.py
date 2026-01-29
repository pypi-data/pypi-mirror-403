from typing import Literal, Optional

from pydantic import BaseModel

class NodeInputPortSchema(BaseModel):
    """
    节点的输入端口定义数据
    """
    name: str
    type: str
    default_value: Optional[str | float | bool | int] = None


class NodeOutputPortSchema(BaseModel):
    """
    节点的输出端口定义数据
    """
    name: str
    type: str


class NodeTypeSchema(BaseModel):
    """
    节点的定义数据
    """
    name: str
    is_trigger: bool
    inputs: dict[str, NodeInputPortSchema]
    outputs: dict[str, NodeOutputPortSchema]
