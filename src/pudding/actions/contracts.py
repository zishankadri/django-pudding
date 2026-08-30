from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pudding.ui import Frame

from django.http import HttpRequest, HttpResponse


@runtime_checkable
class Action(Protocol):
    slug: str
    icon: str | None
    permission: Callable[[HttpRequest], bool] | None

    def handle(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse: ...


type ActionStep = Callable[[Action, HttpRequest, dict[str, Any]], HttpResponse]


@dataclass(frozen=True, slots=True)
class ActionHook:
    frame: Frame
    before: ActionStep
