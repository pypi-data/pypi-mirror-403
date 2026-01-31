"""Node classes for the computation DAG."""

from dataclasses import dataclass
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from formularity_dag.graph import ComputeGraph


@dataclass
class Port:
    """Represents a connection point on a node."""
    name: str
    node: 'Node'


class Node:
    """Base class for all nodes in the computation graph."""

    def __init__(self, name: str):
        self.name: str = name
        self.input_ports: Dict[str, Port] = {}
        self.output_ports: Dict[str, List[Port]] = {}


class InputNode(Node):
    """
    Node representing a user-provided input value.

    InputNodes are leaf nodes in the DAG that receive values from external sources.
    """

    def __init__(
        self,
        name: str,
        dtype: type,
        description: str = "",
        default_val: Any = None,
        is_required: bool = True
    ):
        super().__init__(name)
        self.dtype: type = dtype
        self.description: str = description
        self.default_val: Any = default_val
        self.is_required: bool = is_required
        # Create default output port
        port = Port(name, self)
        self.output_ports[name] = [port]


class ContextNode(InputNode):
    """
    Node representing environment/context parameters.

    ContextNodes are a special type of InputNode for parameters that
    are typically set once and shared across evaluations (e.g., config values).
    """

    def __init__(
        self,
        name: str,
        dtype: type,
        description: str = "",
        default_val: Any = None,
        is_required: bool = True
    ):
        super().__init__(name, dtype, description, default_val, is_required)
