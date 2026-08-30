from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from django.http import HttpRequest
from django.utils.html import format_html, format_html_join

from pudding import ui
from pudding.ui.utils import (
    build_render_context,
)


@dataclass(kw_only=True)
class Component(ABC):
    local_context: dict[str, Any] = field(default_factory=dict)

    def render(
        self, request: HttpRequest | None = None, ctx: dict[str, Any] | None = None
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)
        return self.on_render(request=request, ctx=ctx)

    @abstractmethod
    def on_render(self, request: HttpRequest, ctx: dict[str, Any]) -> str: ...

    def with_local_context(self, **kwargs: Any) -> Component:
        new_context = {**self.local_context, **kwargs}
        return replace(self, local_context=new_context)


@dataclass
class Div(Component):
    children: Sequence[ui.Renderable | str | None] | None = None
    css: str = ""

    def on_render(self, request, ctx: dict[str, Any]) -> str:
        children_list = self.children or []
        rendered_children = format_html_join(
            "",
            "{}",
            (
                (to_html(child, request=request, ctx=ctx),)
                for child in children_list
                if child is not None
            ),
        )
        return format_html(
            '<div class="{css}">{children}</div>',
            css=self.css,
            children=rendered_children,
        )

    def __call__(self, **kwargs) -> Div:
        return replace(self, **kwargs)


def to_html(
    content: ui.Renderable | str | None, request: HttpRequest, ctx: dict[str, Any]
) -> str:
    if content is None:
        return ""
    if isinstance(content, ui.Renderable):
        return content.render(request=request, ctx=ctx)
    if isinstance(content, str):
        return content

    raise TypeError(
        f"Expected content to be Renderable or str, got {type(content).__name__}"
    )
