"""
A factory for pydantic fields.
"""

import inspect
import random
from collections.abc import Callable
from types import UnionType
from typing import Any, Generic, TypeGuard, TypeVar, cast, get_args

from faker import Faker

from pydantricks.model_factory import ModelFactory, T
from pydantricks.shared_utils.infer import (
    is_enum,
    is_literal,
    is_sequence,
    is_union,
)

K = TypeVar("K")
F = TypeVar("F")


def is_model_factory(typ: Any) -> TypeGuard[ModelFactory[Any]]:
    return inspect.isclass(typ) and issubclass(typ, ModelFactory)


class GenericFakerFieldFactory(Generic[F, K]):
    """
    A factory that will be called during model construction.
    The faker instance has to be configured before calling the field factory.

    :param faker: A configured faker instance
    """

    def __init__(self, faker: Faker) -> None:
        self.faker = faker

    @property
    def field(self) -> Faker:
        """Factory for simple types."""
        return self.faker

    def choice(
        self, factory: type[F] | Callable[..., F] | UnionType | ModelFactory[T] | str
    ) -> Callable[[], F]:
        """Factory for composed types such as union, enum, literal and Model factory."""
        if is_literal(factory):
            choices = get_args(factory)
            return lambda: random.choice(choices)

        if is_union(factory):
            choices = get_args(factory)
            return lambda: random.choice(choices)()

        if is_model_factory(factory):
            # T -> F
            return cast(Callable[[], F], factory)

        if is_enum(factory) and is_sequence(factory):
            enum_choices = list(factory)
            return lambda: random.choice(enum_choices)

        if callable(factory):
            return factory

        if is_sequence(factory):
            return lambda: random.choice(factory)

        raise NotImplementedError(factory)

    def set_factory(
        self, factory: type[F], min: int, max: int | None = None
    ) -> Callable[..., set[F]]:
        """Factory for the set type."""

        def callback() -> set[F]:
            size = random.randint(min, max or min)
            ret: set[F] = set()
            while len(ret) < size:
                ret.add(self.choice(factory)())
            return ret

        return callback

    def list_factory(
        self, factory: type[F] | Callable[..., F], min: int, max: int | None = None
    ) -> Callable[..., list[F]]:
        """Factory for the list type."""
        return lambda: [
            self.choice(factory)() for _ in range(random.randint(min, max or min))
        ]

    def tuple_factory(self, *factory: Any) -> Callable[..., tuple[F, ...]]:
        """Factory for the type type."""
        return lambda: tuple(self.choice(f)() for f in factory)

    def dict_factory(
        self,
        key_factory: K,
        value_factory: F,
        min: int,
        max: int,
    ) -> Callable[..., dict[K, F]]:
        """Factory for the dict type."""
        item_factory = self.tuple_factory(key_factory, value_factory)
        return lambda: dict(self.list_factory(item_factory, min, max)())  # type: ignore


FakerFieldFactory = GenericFakerFieldFactory[Any, Any]
"""A factory of FieldFactory."""

FieldFactory = FakerFieldFactory(Faker())
"""A ready to play field factory."""
