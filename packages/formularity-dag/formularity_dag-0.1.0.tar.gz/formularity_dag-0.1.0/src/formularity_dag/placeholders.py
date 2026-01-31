"""Placeholder classes for declaring inputs in user modules."""

import inspect
from typing import Any

from formularity_dag.graph import _get_graph_globals


class InputPlaceholder:
    """
    Placeholder for declaring an input node in a user module.

    When instantiated in a user module, this creates or retrieves that module's
    ComputeGraph and registers a new InputNode.

    Example:
        from formularity_dag import InputPlaceholder

        price = InputPlaceholder("price", float, "Item price", default_val=10.0)
        quantity = InputPlaceholder("quantity", int, "Number of items", default_val=1)
    """

    def __init__(
        self,
        name: str,
        dtype: type,
        description: str = "",
        default_val: Any = None,
        is_required: bool = True
    ):
        # Grab the caller's module globals
        caller_globals = inspect.currentframe().f_back.f_globals
        graph = _get_graph_globals(caller_globals)
        self.node = graph.add_input(name, dtype, description, default_val, is_required)


class ContextPlaceholder:
    """
    Placeholder for declaring a context node in a user module.

    Context nodes are a special type of input for environment/context parameters
    that are typically set once and shared across evaluations.

    Example:
        from formularity_dag import ContextPlaceholder

        tax_rate = ContextPlaceholder("tax_rate", float, "Tax rate", default_val=0.1)
        config = ContextPlaceholder("config", Config, "App config", default_val=Config())
    """

    def __init__(
        self,
        name: str,
        dtype: type,
        description: str = "",
        default_val: Any = None,
        is_required: bool = True
    ):
        # Grab the caller's module globals
        caller_globals = inspect.currentframe().f_back.f_globals
        graph = _get_graph_globals(caller_globals)
        self.node = graph.add_context(name, dtype, description, default_val, is_required)
