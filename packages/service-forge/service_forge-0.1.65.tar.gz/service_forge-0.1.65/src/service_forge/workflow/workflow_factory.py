import uuid
from typing import Callable, Awaitable, AsyncIterator, Any
from copy import deepcopy

from pydantic import ValidationError
from loguru import logger

from .workflow_callback import BuiltinWorkflowCallback
from .workflow import Workflow
from .workflow_group import WorkflowGroup, WORKFLOW_DEFAULT_VERSION
from .workflow_config import WorkflowConfig, WorkflowGroupConfig
from .node import Node, node_register
from .nodes import *
from .triggers import *
from .edge import Edge
from .port import Port, parse_port_name, create_workflow_input_port, create_sub_workflow_input_port
from .context import Context
from .registry.sf_base_model import sf_basemodel_register
from ..service_config import EntryConfig
from ..db.database import DatabaseManager
from ..llm import SfLLM

def parse_argument(arg: Any, service_env: dict[str, Any] = None) -> Any:
    # TODO: deprecated, remove in future
    if type(arg) == str and arg.startswith(f'<{{') and arg.endswith(f'}}>'):
        key = arg[2:-2]
        if key not in service_env:
            raise ValueError(f"Key {key} not found in service env.")
        return service_env[key]

    if isinstance(arg, str) and arg.startswith("SfBaseModel."):
        model_name = arg[len("SfBaseModel."):]
        if sf_basemodel_register.exists(model_name):
            logger.debug(f"Using SfBaseModel {model_name}.")
            return sf_basemodel_register.get(model_name)

    return arg

def create_workflow(
    config_path: str = None,
    config: WorkflowConfig = None,
    entry_config: EntryConfig = None,
    service_env: dict[str, Any] = None,
    workflows: WorkflowGroup = None,
    _handle_stream_output: Callable[[str, AsyncIterator[str]], Awaitable[None]] | None = None,
    _handle_query_user: Callable[[str, str], Awaitable[str]] | None = None,
    database_manager: DatabaseManager = None,
    llm: SfLLM = None,
    debug_version: bool = False,
) -> Workflow:
    if config is None:
        if config_path is not None:
            config = WorkflowConfig.from_yaml_file(config_path)
        else:
            raise ValueError("Either config_path or config must be provided")
    
    workflow = Workflow(
        id = uuid.uuid4(),
        config = config,
        entry_config = entry_config,
        nodes = [],
        input_ports = [],
        output_ports = [],
        _handle_stream_output = _handle_stream_output,
        _handle_query_user = _handle_query_user,
        database_manager = database_manager,
        llm = llm,
        # TODO: max_concurrent_runs
        callbacks = [BuiltinWorkflowCallback()],
        debug_version = debug_version,
        global_context = Context(variables={}),
    )

    nodes: dict[str, Node] = {}

    for node_config in config.nodes:
        params = {
            "name": node_config.name,
        }
        
        node: Node = node_register.instance(node_config.type, ignore_keys=['type'], kwargs=params)

        # Context
        node.context = Context(variables = {})

        # Input ports
        node.input_ports = deepcopy(node.DEFAULT_INPUT_PORTS)
        for input_port in node.input_ports:
            input_port.node = node

        # Output ports
        node.output_ports = deepcopy(node.DEFAULT_OUTPUT_PORTS)
        for output_port in node.output_ports:
            output_port.node = node
        
        # Sub workflows
        if node_config.sub_workflows is not None:
            sub_workflows: WorkflowGroup = WorkflowGroup(workflows=[])
            for sub_workflow_config in node_config.sub_workflows:
                sub_workflow = workflows.get_workflow_by_name(sub_workflow_config.name, sub_workflow_config.version)
                sub_workflows.add_workflow(deepcopy(sub_workflow))
            node.sub_workflows = sub_workflows

        # Sub workflows input ports
        if node_config.sub_workflows_input_ports is not None:
            for sub_workflow_input_port_config in node_config.sub_workflows_input_ports:
                name = sub_workflow_input_port_config.name
                sub_workflow_name, sub_workflow_port_name = parse_port_name(sub_workflow_input_port_config.port)
                sub_workflow = node.sub_workflows.get_workflow_by_name(sub_workflow_name, sub_workflow_config.version)
                if sub_workflow is None:
                    raise ValueError(f"{sub_workflow_name} is not a valid sub workflow.")
                sub_workflow_port = sub_workflow.get_input_port_by_name(sub_workflow_port_name)
                if sub_workflow_port is None:
                    raise ValueError(f"{sub_workflow_port_name} is not a valid input port.")
                value = sub_workflow_input_port_config.value
                node.input_ports.append(create_sub_workflow_input_port(name=name, node=node, port=sub_workflow_port, value=value))

        # Sub workflows output ports
        ...

        # Hooks
        if _handle_query_user is None:
            node.query_user = workflow.handle_query_user
        else:
            node.query_user = _handle_query_user

        nodes[node_config.name] = node

    # Edges
    for node_config in config.nodes:
        start_node = nodes[node_config.name]
        if node_config.outputs is not None:
            for key, value in node_config.outputs.items():
                if value is None:
                    continue

                if type(value) is str:
                    value = [value]

                for edge_value in value:
                    end_node_name, end_port_name = parse_port_name(edge_value)
                    end_node = nodes[end_node_name]

                    start_node.try_create_extended_output_port(key)
                    end_node.try_create_extended_input_port(end_port_name)

                    start_port = start_node.get_output_port_by_name(key)
                    end_port = end_node.get_input_port_by_name(end_port_name)

                    if start_port is None:
                        raise ValueError(f"{key} is not a valid output port.")
                    if end_port is None:
                        raise ValueError(f"{end_port_name} is not a valid input port.")

                    edge = Edge(start_node, end_node, start_port, end_port)

                    start_node.output_edges.append(edge)
                    end_node.input_edges.append(edge)

    workflow.add_nodes(list(nodes.values()))
    
    # Inputs
    if config.inputs is not None:
        for port_config in config.inputs:
            name = port_config.name
            node_name, node_port_name = parse_port_name(port_config.port)
            if node_name not in nodes:
                raise ValueError(f"{node_name} is not a valid node.")
            node = nodes[node_name]
            port = node.get_input_port_by_name(node_port_name)
            if port is None:
                raise ValueError(f"{node_port_name} is not a valid input port.")
            value = port_config.value
            workflow.input_ports.append(create_workflow_input_port(name=name, port=port, value=value))

    # Outputs
    if config.outputs is not None:
        for port_config in config.outputs:
            name = port_config.name
            node_name, node_port_name = parse_port_name(port_config.port)
            if node_name not in nodes:
                raise ValueError(f"{node_name} is not a valid node.")
            node = nodes[node_name]
            port = node.get_output_port_by_name(node_port_name)
            if port is None:
                raise ValueError(f"{node_port_name} is not a valid output port.")
            output_port = Port(name=name, type=Any, port=port)
            workflow.output_ports.append(output_port)
            edge = Edge(node, None, port, output_port)
            node.output_edges.append(edge)

    for node_config in config.nodes:
        node = nodes[node_config.name]
        # Arguments
        if node_config.args is not None:
            for key, value in node_config.args.items():
                node.fill_input_by_name(key, parse_argument(value, service_env=service_env))

    return workflow

def create_workflow_group(
    config_path: str = None,
    config: WorkflowConfig | WorkflowGroupConfig = None,
    entry_config: EntryConfig = None,
    service_env: dict[str, Any] = None,
    _handle_stream_output: Callable[[str, AsyncIterator[str]], Awaitable[None]] = None,
    _handle_query_user: Callable[[str, str], Awaitable[str]] = None,
    database_manager: DatabaseManager = None,
    llm: SfLLM = None,
    debug_version: bool = False,
) -> WorkflowGroup:

    if config is None:
        if config_path is not None:
            try:
                config = WorkflowGroupConfig.from_yaml_file(config_path)
            except:
                config = WorkflowConfig.from_yaml_file(config_path)
        else:
            raise ValueError("Either config_path or config must be provided")

    if isinstance(config, dict):
        try:
            config = WorkflowConfig.model_validate(config)
        except ValidationError:
            config = WorkflowGroupConfig.model_validate(config)

    if type(config) == WorkflowConfig:
        workflow = create_workflow(
            config_path=config_path if config_path else None,
            config=config,
            entry_config=entry_config,
            service_env=service_env,
            _handle_stream_output=_handle_stream_output,
            _handle_query_user=_handle_query_user,
            database_manager=database_manager,
            llm=llm,
            debug_version=debug_version,
        )
        return WorkflowGroup(workflows=[workflow], main_workflow_name=workflow.name, main_workflow_version=workflow.version)
    elif type(config) == WorkflowGroupConfig:
        workflows = WorkflowGroup(
            workflows=[],
            main_workflow_name=config.main_workflow_name,
            main_workflow_version=config.main_workflow_version,
        )
        for workflow_config in config.workflows:
            workflows.add_workflow(create_workflow(
                config=workflow_config,
                entry_config=entry_config,
                workflows=workflows,
                service_env=service_env,
                _handle_stream_output=_handle_stream_output,
                _handle_query_user=_handle_query_user,
                database_manager=database_manager,
                llm=llm,
                debug_version=debug_version,
            ))
        return workflows
