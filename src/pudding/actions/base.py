from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed

from pudding.actions.contracts import ActionHook, ActionStep
from pudding.ui import Trigger
from pudding.ui.primitives.triggers import Trigger as CoreTrigger


@dataclass(kw_only=True)
class InteractiveAction(ABC):
    """
    Base class for actions requiring user interaction (like confirmation or forms)
    before the backend logic runs.
    """

    slug: str
    icon: str | None = None
    permission: Callable[[HttpRequest], bool] | None = None

    def handle(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        match request.method:
            case "GET":
                return self.before(request, ctx)
            case "POST":
                return self.execute(request, ctx)
            case _:
                return HttpResponseNotAllowed(["GET", "POST"])

    @abstractmethod
    def before(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse: ...

    @abstractmethod
    def execute(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse: ...


@dataclass(kw_only=True)
class FunctionalInteractiveAction:
    slug: str
    trigger: CoreTrigger
    icon: str | None = None
    permission: Callable[[HttpRequest], bool] | None = None

    execute: ActionStep | None = None
    before: ActionStep | None = None

    allowed_methods: list[str] = field(init=False, repr=False)

    def __post_init__(self):
        allowed = []
        if self.before:
            allowed.append("GET")
        if self.execute:
            allowed.append("POST")

        if not allowed:
            raise ValueError("At least one of `execute` or `before` must be provided.")

        self.allowed_methods = allowed

    def handle(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        if request.method == "GET" and self.before:
            return self.before(self, request, ctx)

        if request.method == "POST" and self.execute:
            return self.execute(self, request, ctx)

        return HttpResponseNotAllowed(self.allowed_methods)

    def __repr__(self):
        return (
            f"FunctionalAction("
            f"slug={self.slug!r}, "
            f"execute={getattr(self.execute, '__name__', None)!r}, "
            f"before={getattr(self.before, '__name__', None)!r})"
        )


def interactive_action(
    *,
    slug: str,
    label: str | None = None,
    icon: str | None = None,
    before: ActionHook | Callable | None = None,
    permission: Callable[[HttpRequest], bool] | None = None,
) -> Callable[[Callable], FunctionalInteractiveAction]:
    def decorator(func: Callable) -> FunctionalInteractiveAction:

        display_label = label or slug.replace("_", " ").replace("-", " ").capitalize()
        trigger = Trigger.action(
            slug,
            label=display_label,
            icon=icon,
        )

        before_func = None

        if isinstance(before, ActionHook):
            frame = before.frame
            before_func = before.before
            trigger = trigger(**frame.loading_mod)
        elif callable(before):
            before_func = before

        action = FunctionalInteractiveAction(
            slug=slug,
            icon=icon,
            trigger=trigger,
            execute=func,
            before=before_func,
            permission=permission,
        )

        return action

    return decorator


@dataclass(kw_only=True)
class BasicAction:
    slug: str
    icon: str | None = None
    handler: ActionStep
    trigger: CoreTrigger | None = None

    permission: Callable[[HttpRequest], bool] | None = None

    def handle(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        return self.handler(self, request, ctx)

    def __repr__(self):
        return f"BasicAction(slug={self.slug!r}, handler={self.handler.__name__!r})"


def action_handler(
    *,
    slug: str,
    label: str | None = None,
    icon: str | None = None,
    permission: Callable[[HttpRequest], bool] | None = None,
) -> Callable[[ActionStep], BasicAction]:
    def decorator(func: ActionStep) -> BasicAction:
        display_label = label or slug.replace("_", " ").replace("-", " ").capitalize()
        trigger = Trigger.action(slug, label=display_label, icon=icon)

        return BasicAction(
            slug=slug,
            handler=func,
            trigger=trigger,
            icon=icon,
            permission=permission,
        )

    return decorator
