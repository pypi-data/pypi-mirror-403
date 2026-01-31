"""Core computation graph container and StateNode."""

import inspect
from dataclasses import is_dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from formularity_dag.nodes import Node, Port, InputNode, ContextNode
from formularity_dag.utils import is_dataclass_type, dataclass_to_dict, dict_to_dataclass


class StateNode(Node):
    """
    Node representing a computed value based on other nodes.

    StateNodes execute a function with inputs from connected nodes.
    """

    def __init__(
        self,
        graph: 'ComputeGraph',
        func: Callable,
        mapping: Optional[Dict[str, str]] = None,
        is_output: bool = False
    ):
        super().__init__(func.__name__)
        self.graph = graph
        self.func: Callable = func
        self.mapping: Dict[str, str] = mapping or {}
        self.is_output: bool = is_output
        self._bind_ports()

    def _bind_ports(self):
        """Bind input ports based on function parameters and create connections."""
        sig = inspect.signature(self.func)
        for param_name in sig.parameters:
            port = Port(param_name, self)
            self.input_ports[param_name] = port

            # Find source node/port
            src_key = self.mapping.get(param_name, param_name)
            src_node = self.graph.nodes.get(src_key)
            if not src_node:
                raise ValueError(f"No node named '{src_key}' for parameter '{param_name}'")
            src_ports = src_node.output_ports.get(src_key)
            if not src_ports:
                raise ValueError(f"No output port '{src_key}' on node '{src_key}'")
            # Connect first port by default
            src_port = src_ports[0]
            self.graph.connections.append((src_port, port))

        # Create default output port
        out_port = Port(self.name, self)
        self.output_ports[self.name] = [out_port]


def _get_graph_globals(globals_dict: Dict[str, Any]) -> 'ComputeGraph':
    """Get or create the ComputeGraph for a module's globals."""
    if '__compute_graph__' not in globals_dict:
        globals_dict['__compute_graph__'] = ComputeGraph()
    return globals_dict['__compute_graph__']


class ComputeGraph:
    """
    Container for a computation graph.

    A ComputeGraph holds nodes (inputs, contexts, states) and their connections,
    and provides methods to evaluate the graph with given inputs.
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.connections: List[Tuple[Port, Port]] = []

    def add_input(
        self,
        name: str,
        dtype: type,
        description: str = "",
        default_val: Any = None,
        is_required: bool = True
    ) -> InputNode:
        """Add an input node to the graph."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists")
        node = InputNode(name, dtype, description, default_val, is_required)
        self.nodes[name] = node
        return node

    def add_context(
        self,
        name: str,
        dtype: type,
        description: str = "",
        default_val: Any = None,
        is_required: bool = True
    ) -> ContextNode:
        """Add a context node to the graph."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists")
        node = ContextNode(name, dtype, description, default_val, is_required)
        self.nodes[name] = node
        return node

    def add_state(
        self,
        func: Callable,
        mapping: Optional[Dict[str, str]] = None,
        is_output: bool = False
    ) -> StateNode:
        """Add a state (computed) node to the graph."""
        if func.__name__ in self.nodes:
            raise ValueError(f"Node '{func.__name__}' already exists")
        node = StateNode(self, func, mapping, is_output)
        self.nodes[node.name] = node
        return node

    def _topological_order(self) -> List[Node]:
        """Return nodes in topological order for evaluation."""
        nodes = list(self.nodes.values())
        edges: Dict[str, List[str]] = {node.name: [] for node in nodes}
        indegree: Dict[str, int] = {node.name: 0 for node in nodes}

        for src_port, dst_port in self.connections:
            src_name = src_port.node.name
            dst_name = dst_port.node.name
            if dst_name not in edges[src_name]:
                edges[src_name].append(dst_name)
                indegree[dst_name] += 1

        queue = [self.nodes[name] for name, degree in indegree.items() if degree == 0]
        order: List[Node] = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for dst_name in edges[node.name]:
                indegree[dst_name] -= 1
                if indegree[dst_name] == 0:
                    queue.append(self.nodes[dst_name])

        if len(order) != len(nodes):
            raise ValueError("Compute graph has at least one cycle")
        return order

    def evaluate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the compute graph and return structured results.

        Args:
            inputs: Dictionary mapping input/context node names to values.

        Returns:
            Dict with keys:
                - 'timestamp': evaluation timestamp
                - 'inputs': dict of input node values
                - 'context': dict of context node values
                - 'state': dict of state node values
                - 'outputs': dict of output-tagged state node values
                - 'all_values': dict of all node values
        """
        values: Dict[str, Any] = {}
        result: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'inputs': {},
            'context': {},
            'state': {},
            'outputs': {},
            'all_values': {}
        }

        # Process input nodes
        for node in self.nodes.values():
            if isinstance(node, InputNode):
                # Handle missing/None values for optional inputs
                if node.name not in inputs or inputs[node.name] is None:
                    if node.is_required:
                        raise ValueError(f"Missing required input for '{node.name}'")
                    else:
                        values[node.name] = None
                        stored_value = None
                        if isinstance(node, ContextNode):
                            result['context'][node.name] = stored_value
                        else:
                            result['inputs'][node.name] = stored_value
                        continue

                value = inputs[node.name]

                # Handle dataclass conversion
                if node.dtype is not None and is_dataclass_type(node.dtype):
                    if isinstance(value, dict):
                        value = dict_to_dataclass(value, node.dtype)
                    elif not isinstance(value, node.dtype):
                        raise TypeError(f"Input '{node.name}' expects {node.dtype.__name__}")
                elif node.dtype is not None and not isinstance(value, node.dtype):
                    raise TypeError(f"Input '{node.name}' expects {node.dtype.__name__}")

                values[node.name] = value

                # Categorize the input (serialize dataclasses for storage)
                stored_value = dataclass_to_dict(value) if is_dataclass_type(node.dtype) else value
                if isinstance(node, ContextNode):
                    result['context'][node.name] = stored_value
                else:
                    result['inputs'][node.name] = stored_value

        # Build source lookup
        src_by_dst: Dict[Tuple[str, str], Node] = {}
        for src_port, dst_port in self.connections:
            key = (dst_port.node.name, dst_port.name)
            if key in src_by_dst:
                raise ValueError(f"Multiple sources for input '{dst_port.name}' on '{dst_port.node.name}'")
            src_by_dst[key] = src_port.node

        # Evaluate state nodes in topological order
        for node in self._topological_order():
            if isinstance(node, InputNode):
                continue
            if isinstance(node, StateNode):
                kwargs: Dict[str, Any] = {}
                for param_name in node.input_ports.keys():
                    src_node = src_by_dst.get((node.name, param_name))
                    if not src_node:
                        raise ValueError(f"Unbound input '{param_name}' for node '{node.name}'")
                    if src_node.name not in values:
                        raise ValueError(f"Missing value for node '{src_node.name}'")
                    kwargs[param_name] = values[src_node.name]
                value = node.func(**kwargs)
                values[node.name] = value
                result['state'][node.name] = value

                if node.is_output:
                    result['outputs'][node.name] = value

        # Serialize all values
        serialized_values = {}
        for name, value in values.items():
            node = self.nodes[name]
            if isinstance(node, InputNode) and is_dataclass_type(node.dtype):
                serialized_values[name] = dataclass_to_dict(value)
            else:
                serialized_values[name] = value

        result['all_values'] = serialized_values
        return result

    def get_node_metadata(self) -> Dict[str, Any]:
        """
        Return metadata about all nodes in the graph for UI rendering.

        Returns:
            Dict with 'nodes' (list of node info) and 'edges' (list of edge info).
        """
        nodes_info = []
        edges_info = []

        for node in self.nodes.values():
            node_info = {
                'id': node.name,
                'name': node.name,
            }

            if isinstance(node, ContextNode):
                node_info['type'] = 'context'
                node_info['dtype'] = node.dtype.__name__ if node.dtype else 'any'
                node_info['description'] = node.description
                node_info['is_dataclass'] = is_dataclass_type(node.dtype) if node.dtype else False
                default_val = node.default_val
                if default_val is not None and is_dataclass(default_val):
                    default_val = dataclass_to_dict(default_val)
                node_info['default_val'] = default_val
                node_info['is_required'] = node.is_required
            elif isinstance(node, InputNode):
                node_info['type'] = 'input'
                node_info['dtype'] = node.dtype.__name__ if node.dtype else 'any'
                node_info['description'] = node.description
                node_info['is_dataclass'] = is_dataclass_type(node.dtype) if node.dtype else False
                default_val = node.default_val
                if default_val is not None and is_dataclass(default_val):
                    default_val = dataclass_to_dict(default_val)
                node_info['default_val'] = default_val
                node_info['is_required'] = node.is_required
            elif isinstance(node, StateNode):
                node_info['type'] = 'state'
                node_info['is_output'] = node.is_output
                node_info['inputs'] = list(node.input_ports.keys())
            else:
                node_info['type'] = 'unknown'

            nodes_info.append(node_info)

        for src_port, dst_port in self.connections:
            edges_info.append({
                'source': src_port.node.name,
                'target': dst_port.node.name,
                'label': dst_port.name,
            })

        return {
            'nodes': nodes_info,
            'edges': edges_info,
        }

    def __repr__(self):
        return f"ComputeGraph(nodes={list(self.nodes.keys())}, connections={len(self.connections)})"
