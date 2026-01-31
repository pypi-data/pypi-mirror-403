"""
formularity_dag - A declarative Python framework for building computation DAGs.

This package provides a simple way to define computation graphs where:
- Input nodes represent user-provided values
- Context nodes represent environment/configuration parameters
- State nodes represent computed values based on other nodes
- The @compute decorator automatically wires up dependencies

Example:
    from formularity_dag import InputPlaceholder, compute, formula_dataclass

    @formula_dataclass
    class Config:
        tax_rate: float = 0.1

    price = InputPlaceholder("price", float, "Item price", default_val=10.0)
    quantity = InputPlaceholder("quantity", int, "Number of items", default_val=1)

    @compute
    def subtotal(price, quantity):
        return price * quantity

    @compute(is_output=True)
    def total(subtotal, config):
        return subtotal * (1 + config.tax_rate)
"""

from dataclasses import field

from formularity_dag.graph import ComputeGraph, StateNode, _get_graph_globals
from formularity_dag.nodes import Node, Port, InputNode, ContextNode
from formularity_dag.placeholders import InputPlaceholder, ContextPlaceholder
from formularity_dag.decorators import compute, formula_dataclass
from formularity_dag.utils import is_dataclass_type, dataclass_to_dict, dict_to_dataclass

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "ComputeGraph",
    "Node",
    "Port",
    "InputNode",
    "ContextNode",
    "StateNode",
    # Placeholders
    "InputPlaceholder",
    "ContextPlaceholder",
    # Decorators
    "compute",
    "formula_dataclass",
    # Dataclass utilities
    "field",
    "is_dataclass_type",
    "dataclass_to_dict",
    "dict_to_dataclass",
]
