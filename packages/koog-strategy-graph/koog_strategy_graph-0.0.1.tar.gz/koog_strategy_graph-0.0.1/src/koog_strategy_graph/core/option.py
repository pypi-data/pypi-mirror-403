from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar, cast

T = TypeVar("T")
U = TypeVar("U")


class Option(ABC, Generic[T]):
    """
    Minimal Option type mirroring Koog's Option/Some/Empty semantics.
    Used to indicate whether an edge is "taken" (Some) or "skipped" (Empty).
    """

    @property
    @abstractmethod
    def is_empty(self) -> bool:
        raise AssertionError("abstract")

    @property
    @abstractmethod
    def value(self) -> T:
        raise AssertionError("abstract")

    def map(self, fn: Callable[[T], U]) -> "Option[U]":
        if self.is_empty:
            return empty()
        return Some(fn(self.value))

    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        if self.is_empty:
            return empty()
        return self if predicate(self.value) else empty()

    def get_or_none(self) -> Optional[T]:
        return None if self.is_empty else self.value


@dataclass(frozen=True)
class Some(Option[T]):
    _value: T

    @property
    def is_empty(self) -> bool:
        return False

    @property
    def value(self) -> T:
        return self._value


@dataclass(frozen=True)
class Empty(Option[None]):
    @property
    def is_empty(self) -> bool:
        return True

    @property
    def value(self) -> None:
        raise ValueError("Empty has no value")


_EMPTY = Empty()


def empty() -> Option[T]:
    """
    Typed Empty instance.

    Note: `Option[T]` is invariant, so `Empty()` (which is `Option[None]`) isn't
    assignable to `Option[T]` without an explicit cast.
    """

    return cast(Option[T], _EMPTY)

