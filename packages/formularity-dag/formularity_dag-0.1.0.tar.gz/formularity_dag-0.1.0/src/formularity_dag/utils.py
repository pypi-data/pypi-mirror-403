"""Dataclass utility functions for formularity_dag."""

from dataclasses import is_dataclass, asdict
from typing import Any, Dict


def is_dataclass_type(dtype: type) -> bool:
    """Check if a type is a dataclass."""
    return dtype is not None and is_dataclass(dtype)


def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert a dataclass instance to a dictionary.

    Supports both standard dataclasses and dataclasses-json enhanced classes.
    """
    if hasattr(obj, 'to_dict'):
        # If using dataclasses-json
        return obj.to_dict()
    elif is_dataclass(obj):
        # Fallback to standard dataclasses
        return asdict(obj)
    else:
        raise TypeError(f"Object {obj} is not a dataclass")


def dict_to_dataclass(data: Dict[str, Any], dtype: type) -> Any:
    """
    Convert a dictionary to a dataclass instance.

    Supports both standard dataclasses and dataclasses-json enhanced classes.
    """
    if hasattr(dtype, 'from_dict'):
        # If using dataclasses-json
        return dtype.from_dict(data)
    elif is_dataclass(dtype):
        # Fallback to standard dataclasses
        return dtype(**data)
    else:
        raise TypeError(f"Type {dtype} is not a dataclass")
