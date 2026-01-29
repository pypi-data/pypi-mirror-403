"""
Result object utilities for InstaVM SDK

Provides object-based access to execution results instead of dict-based access.
Example: result.stdout instead of result['stdout']
"""
from types import SimpleNamespace
from typing import Any, Dict, List, Union

SCHEMA_VERSION = "1.0"


class ExecutionResult(SimpleNamespace):
    """
    Object-based execution result with attribute access.

    Supports:
    - result.stdout
    - result.stderr
    - result.execution_time
    - result.cpu_time
    - Nested dict/list conversion
    - Schema versioning

    Also supports dict-style access for backward compatibility:
    - result['stdout']
    """

    def __getitem__(self, key):
        """Support dict-style access for backward compatibility"""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Support dict-style assignment for backward compatibility"""
        setattr(self, key, value)

    def __contains__(self, key):
        """Support 'in' operator for backward compatibility"""
        return hasattr(self, key)

    def get(self, key, default=None):
        """Support dict.get() for backward compatibility"""
        return getattr(self, key, default)

    def keys(self):
        """Support dict.keys() for backward compatibility"""
        return self.__dict__.keys()

    def values(self):
        """Support dict.values() for backward compatibility"""
        return self.__dict__.values()

    def items(self):
        """Support dict.items() for backward compatibility"""
        return self.__dict__.items()

    def to_dict(self) -> Dict:
        """Convert back to plain dict"""
        return obj_to_dict(self)

    def __repr__(self):
        items = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"ExecutionResult({items})"


def dict_to_obj(d: Any) -> Any:
    """
    Recursively convert dict to object with attribute access.

    Args:
        d: Dict, list, or primitive value

    Returns:
        ExecutionResult for dicts, list for lists, primitives unchanged

    Example:
        >>> result = dict_to_obj({'stdout': 'hello', 'stderr': ''})
        >>> result.stdout
        'hello'
    """
    if isinstance(d, dict):
        return ExecutionResult(**{k: dict_to_obj(v) for k, v in d.items()})
    elif isinstance(d, list):
        return [dict_to_obj(x) for x in d]
    else:
        return d


def obj_to_dict(obj: Any) -> Any:
    """
    Recursively convert object back to dict.

    Args:
        obj: ExecutionResult, SimpleNamespace, list, or primitive

    Returns:
        Plain dict/list/primitive

    Example:
        >>> result = ExecutionResult(stdout='hello', stderr='')
        >>> obj_to_dict(result)
        {'stdout': 'hello', 'stderr': ''}
    """
    if isinstance(obj, (SimpleNamespace, ExecutionResult)):
        return {k: obj_to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [obj_to_dict(x) for x in obj]
    else:
        return obj


def make_execution_result(raw: Dict[str, Any]) -> ExecutionResult:
    """
    Create an ExecutionResult object from API response dict.

    Args:
        raw: Raw dict from API response

    Returns:
        ExecutionResult object with attribute access

    Example:
        >>> raw = {'stdout': 'hello', 'stderr': '', 'execution_time': 1.5}
        >>> result = make_execution_result(raw)
        >>> result.stdout
        'hello'
        >>> result.execution_time
        1.5
        >>> result['stdout']  # Also supports dict-style access
        'hello'
    """
    raw = dict(raw)  # defensive copy
    raw.setdefault("schema_version", SCHEMA_VERSION)
    return dict_to_obj(raw)
