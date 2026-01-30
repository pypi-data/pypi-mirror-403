"""Type inference."""

import inspect
from collections.abc import Sequence
from enum import Enum
from types import UnionType
from typing import Any, Literal, TypeGuard, get_origin


def is_literal(typ: Any) -> bool:
    """Used to detect literal types."""
    type_origin = get_origin(typ)
    if type_origin:
        if type_origin is Literal:
            return True
    return False


def is_union(typ: Any) -> TypeGuard[UnionType]:
    """Used to detect unions like  T | U."""
    type_origin = get_origin(typ)
    if type_origin:
        if type_origin is UnionType:  # T | U
            return True
    return False


def is_sequence(typ: Any) -> TypeGuard[Sequence[Any]]:
    if is_enum(typ):
        return True
    return isinstance(typ, Sequence)


def is_enum(typ: Any) -> TypeGuard[Enum]:
    return inspect.isclass(typ) and issubclass(typ, Enum)
