"""Decorators for defining computation nodes and dataclasses."""

import sys
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from formularity_dag.graph import _get_graph_globals

# Try to import dataclass_json for enhanced serialization
try:
    from dataclasses_json import dataclass_json as _dataclass_json
    HAS_DATACLASS_JSON = True
except ImportError:
    _dataclass_json = None
    HAS_DATACLASS_JSON = False


def formula_dataclass(cls=None, **kwargs):
    """
    Combined decorator that applies both @dataclass and @dataclass_json.

    If dataclasses-json is not installed, only @dataclass is applied.

    Usage:
        @formula_dataclass
        class MyData:
            name: str
            value: int = 0

    This is equivalent to:
        @dataclass_json
        @dataclass
        class MyData:
            name: str
            value: int = 0

    Args:
        cls: The class to decorate (when used without parentheses)
        **kwargs: Arguments passed to @dataclass (e.g., frozen=True)
    """
    def decorator(cls):
        # First apply @dataclass
        dc_cls = dataclass(cls, **kwargs)
        # Then apply @dataclass_json if available
        if HAS_DATACLASS_JSON and _dataclass_json:
            return _dataclass_json(dc_cls)
        return dc_cls

    if cls is None:
        # Called with arguments: @formula_dataclass(frozen=True)
        return decorator
    else:
        # Called without arguments: @formula_dataclass
        return decorator(cls)


def compute(_func=None, *, mapping: Optional[Dict[str, str]] = None, is_output: bool = False):
    """
    Decorator to register a state node in the calling module's compute graph.

    The function's parameters are automatically connected to nodes with matching names.
    Use `mapping` to override parameter-to-node name mapping.

    Usage:
        @compute
        def add(x, y):
            return x + y

        @compute(mapping={'a': 'input1', 'b': 'input2'})
        def multiply(a, b):
            return a * b

        @compute(is_output=True)
        def final_result(multiply):
            return multiply * 2

    Args:
        _func: The function to decorate (when used without parentheses)
        mapping: Dict mapping parameter names to source node names
        is_output: If True, marks this node as a final output
    """
    def decorator(func: Callable):
        # Use the func's module globals for graph
        mod = sys.modules[func.__module__]
        graph = _get_graph_globals(mod.__dict__)
        graph.add_state(func, mapping, is_output)
        return func

    if _func is None:
        return decorator
    else:
        return decorator(_func)
