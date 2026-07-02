from __future__ import annotations

from typing import Callable, TypeVar

_SOURCES: dict[str, type] = {}
_WRITERS: dict[str, type] = {}

T = TypeVar("T")


def register_source(name: str) -> Callable[[type[T]], type[T]]:
    def deco(cls: type[T]) -> type[T]:
        _SOURCES[name] = cls
        return cls
    return deco


def register_writer(name: str) -> Callable[[type[T]], type[T]]:
    def deco(cls: type[T]) -> type[T]:
        _WRITERS[name] = cls
        return cls
    return deco


def get_source(name: str) -> type:
    if name not in _SOURCES:
        raise KeyError(f"Unknown source '{name}'. Available: {sorted(_SOURCES)}")
    return _SOURCES[name]


def get_writer(name: str) -> type:
    if name not in _WRITERS:
        raise KeyError(f"Unknown writer '{name}'. Available: {sorted(_WRITERS)}")
    return _WRITERS[name]
