from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Any, Final, Literal, Protocol, get_args, runtime_checkable

from django.http import HttpRequest


@runtime_checkable
class Renderable(Protocol):
    def render(
        self, request: HttpRequest | None = None, ctx: dict[str, Any] | None = None
    ) -> str: ...


class CompositeRenderable(Renderable, Protocol):
    children: Sequence[Renderable]


type Lazy[T] = T | Callable[..., T]
type AttrValue = Lazy[str] | list[Lazy[str]]
type HtmlAttrs = dict[str, AttrValue]

# Note: Using assignment instead of `type` statement
# because `get_args()` returns () on PEP 695 TypeAliasType objects.
IconSize = Literal["icon", "icon-sm", "icon-md", "icon-lg"]
RegularSize = Literal["normal", "sm", "lg"]
Size = RegularSize | IconSize

_ICON_SIZES: frozenset[str] = frozenset(get_args(IconSize))


def is_icon_size(size: Size) -> bool:
    return size in _ICON_SIZES


@dataclass(frozen=True, slots=True)
class TriggerProps:
    tag: str
    label: str
    icon: str | None
    size: Size
    loading: bool | Literal["indicator-only"]
    attrs: dict[str, Any]

    def __call__(self, **kwargs: Any) -> TriggerProps:
        return replace(self, **kwargs)


type LookType = Callable[[TriggerProps], str]


class UnsetType:
    """A sentinel representing an unset value in the UI framework."""

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET: Final = UnsetType()
