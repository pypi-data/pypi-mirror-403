from typing import Type

from fastapi import APIRouter
from omegaconf import OmegaConf

from service_forge.model.meta_api.schema import NodeTypeSchema, NodeInputPortSchema, NodeOutputPortSchema
from service_forge.sft.config.sf_metadata import load_metadata
from service_forge.workflow.node import Node, node_register
from service_forge.workflow.trigger import Trigger

def _node_class_to_schema(node_class: Type[Node]) -> NodeTypeSchema:
    """将Node子类转化为NodeTypeSchema"""
    _input_ports = {}
    for port in node_class.DEFAULT_INPUT_PORTS:
        _input_ports[port.name] = NodeInputPortSchema(
            name=port.name,
            type=port.type.__name__,
            default_value=port.default
        )

    _output_ports = {}
    for port in node_class.DEFAULT_OUTPUT_PORTS:
        _output_ports[port.name] = NodeOutputPortSchema(
            name=port.name,
            type=port.type.__name__
        )

    return NodeTypeSchema(
        name = node_class.__name__,
        inputs=_input_ports,
        outputs=_output_ports,
        is_trigger=issubclass(node_class, Trigger)
    )


def create_schema_router() -> APIRouter:
    router = APIRouter(prefix='/schema')

    @router.get('/nodes', response_model=list[NodeTypeSchema])
    def get_node_schema():
        schemas = []
        for k, v in node_register.items.items():
            if v is not Trigger:
                schemas.append(_node_class_to_schema(v))
        return schemas

    return router

def create_meta_api_router() -> APIRouter:
    router = APIRouter(tags=['meta-api'], prefix='/sdk/meta-api')
    router.include_router(create_schema_router())
    return router

metadata = load_metadata('sf-meta.yaml')
service_config = OmegaConf.load(metadata.service_config)

meta_api_router = create_meta_api_router()
