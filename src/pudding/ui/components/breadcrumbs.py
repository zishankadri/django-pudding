from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from django.http import HttpRequest
from django.utils.functional import Promise
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from pudding import ui
from pudding.ui.primitives import Trigger as CoreTrigger
from pudding.ui.utils import attrs_to_html, build_render_context


@dataclass(frozen=True, slots=True)
class Breadcrumbs:
    children: Sequence[BreadcrumbLabel | CoreTrigger]
    css: str = field(default_factory=str)
    auto_look: bool = True

    local_context: dict[str, Any] = field(default_factory=dict)

    def render(
        self,
        request: HttpRequest | None = None,
        ctx: dict[str, Any] | None = None,
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        rendered_items: list[str] = []
        for i, child in enumerate(self.children):
            if self.auto_look and isinstance(child, CoreTrigger):
                child = child(look=ui.looks.breadcrumb())

            rendered_items.append(
                format_html("<li>{}</li>", child.render(request=request, ctx=ctx))
            )

            if i != (len(self.children) - 1):
                rendered_items.append(
                    '<li class="text-foreground-light"><i data-lucide="chevron-right"></i></li>'
                )

        rendered = "".join(rendered_items)

        return mark_safe(f"""<nav aria-label="breadcrumbs">
    <ol class="flex items-center text-sm gap-2">
        {rendered}
    </ol>
</nav>
""")

    def __call__(self, **kwargs) -> Breadcrumbs:
        return replace(self, **kwargs)


@dataclass(frozen=True)
class BreadcrumbLabel:
    label: str | Promise
    icon: str | None = None
    active: bool = False
    attrs: dict[str, str] | None = None

    local_context: dict[str, Any] = field(default_factory=dict)

    def render(self, request: HttpRequest, ctx: dict[str, Any] | None = None) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)
        icon_html = ""
        if self.icon:
            icon_html = mark_safe(f'<i data-lucide="{self.icon}"></i>')

        attrs = dict(self.attrs or {})
        css = " active" if self.active else ""
        if attrs_class := attrs.get("class"):
            css += " " + attrs_class
        attrs["class"] = f"breadcrumb {css}".strip()

        return format_html(
            "<span {attrs}>{icon}{label}</span>",
            attrs=attrs_to_html(attrs),
            icon=icon_html,
            label=self.label,
        )
