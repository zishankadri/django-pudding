from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.functional import Promise
from django.utils.html import format_html, format_html_join

from pudding.ui.contracts import (
    HtmlAttrs,
    Lazy,
    LookType,
    Renderable,
    Size,
    TriggerProps,
    is_icon_size,
)
from pudding.ui.utils import (
    build_render_context,
    merge_attrs,
    resolve_attrs,
    resolve_lazy,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Trigger:
    tag: str
    look: LookType
    attrs: HtmlAttrs | None = field(default_factory=dict)

    label: Lazy[str | Promise] = ""
    icon: Lazy[str] | None = None

    size: Lazy[Size] = "normal"

    loading: bool | Literal["indicator-only"] = True
    visible: Lazy[bool | str] = True  # 'str' for required permissions

    local_context: dict[str, Any] = field(default_factory=dict)

    def render(
        self,
        request: HttpRequest | None = None,
        ctx: dict[str, Any] | None = None,
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        icon = self.resolve("icon", ctx)
        size = self.resolve("size", ctx)
        label = self.resolve("label", ctx) if not is_icon_size(size) else ""

        raw_attrs = dict(self.attrs or {})
        attrs = resolve_attrs(raw_attrs, ctx=ctx, node=self)

        return self.look(
            TriggerProps(
                tag=self.tag,
                label=label,
                icon=icon,
                attrs=attrs,
                size=size,
                loading=self.loading,
            )
        )

    def __call__(self, **kwargs: Any) -> Any:
        attrs = self.attrs.copy() if self.attrs else {}
        if "attrs" in kwargs:
            attrs = kwargs.pop("attrs")
            if self.attrs:
                attrs = merge_attrs(self.attrs, attrs)

        return replace(self, **kwargs, attrs=attrs)

    def resolve(self, field_name: str, ctx: dict[str, Any]):
        value_or_func = getattr(self, field_name)
        return resolve_lazy(
            value_or_func=value_or_func, ctx=ctx, node=self, field_name=field_name
        )

    def with_local_context(self, **kwargs: Any) -> Trigger:
        new_context = {**self.local_context, **kwargs}
        return replace(self, local_context=new_context)


@dataclass(frozen=True, slots=True, kw_only=True)
class ActionTrigger(Trigger):
    action_slug: str


@dataclass(frozen=True, slots=True)
class Shell:
    """Visible component with UI chrome and a trigger."""

    children: Sequence[Trigger]
    trigger: Trigger
    template: str

    local_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.children, tuple):
            object.__setattr__(self, "children", tuple(self.children))

    def render(
        self, request: HttpRequest | None = None, ctx: dict[str, Any] | None = None
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        return render_to_string(
            self.template,
            {
                "trigger_html": self.trigger.render(request=request, ctx=ctx),
                "rendered_children": "".join(
                    f"<li>{child.render(request=request, ctx=ctx)}</li>"
                    for child in self.children
                ),
                "ctx": ctx,
            },
        )

    def __call__(self, **kwargs) -> Shell:
        return replace(self, **kwargs)


@dataclass(frozen=True, slots=True)
class Group:
    children: Sequence[Renderable]
    css: str
    local_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.children, tuple):
            object.__setattr__(self, "children", tuple(self.children))

    def render(
        self, request: HttpRequest | None = None, ctx: dict[str, Any] | None = None
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        rendered_children = format_html_join(
            "",
            "{}",
            ((child.render(request=request, ctx=ctx),) for child in self.children),
        )
        return format_html(
            '<div class="{css}">{children}</div>',
            css=self.css,
            children=rendered_children,
        )

    def __call__(self, **kwargs) -> Group:
        return replace(self, **kwargs)
