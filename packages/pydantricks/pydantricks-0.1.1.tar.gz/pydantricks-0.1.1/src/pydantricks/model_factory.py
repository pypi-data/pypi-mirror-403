"""
A factory for pydantic models.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelFactory(Generic[T]):
    """Generic Factory for Pydantic models."""

    def __new__(cls, **overrides: Any) -> T:  # type: ignore
        """Create and return an instance of the Pydantic model."""
        model_type: type[T] = cls.__orig_bases__[0].__args__[0]  # type: ignore

        field_values = overrides.copy()
        for key in model_type.model_fields:
            if key not in field_values:
                if hasattr(cls, key):
                    value = getattr(cls, key)
                    field_values[key] = value() if callable(value) else value
        field_values.update(overrides)
        return model_type(**field_values)
