from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from pudding.ui.contracts import Renderable
from pudding.ui.primitives import Component, Div, Frame, to_html
from pudding.ui.utils import build_sidebar_from_domains

from .frames import breadcrumb_frame, header_triggers_frame, modal_frame, view_frame


@dataclass(kw_only=True)
class Page(Component):
    content: str
    active_sidebar_id: str | None = None
    modal_frame: Frame = modal_frame
    css_files: Sequence[str] = field(default_factory=list)

    def on_render(self, request: HttpRequest, ctx: dict[str, Any]) -> str:
        extra_head = mark_safe(
            "\n".join(
                format_html('<link rel="stylesheet" href="{}">', css_file)
                for css_file in self.css_files
            )
        )

        return render_to_string(
            "pudding/components/page.html",
            request=request,
            context={
                "main": self.content,
                "modal_frame": self.modal_frame.render(request=request),
                "extra_head": extra_head,
            },
        )


DASHBOARD_MAIN_SECTION_HTML = """{sidebar}
<main class="flex-1 overflow-y-auto h-screen pr-3">
    <div class="flex flex-col min-h-screen max-w-[96rem] mx-auto">
        <div class="header-bar">
            {breadcrumbs}
            <div x-data class="flex gap-2 [&_div]:flex [&_div]:gap-2">
                {header_triggers}
            </div>
        </div>
        {view_area}
    </div>
</main>
"""


@dataclass(kw_only=True)
class DashboardPage(Component):
    view_content: Renderable | str | None = None
    breadcrumbs: Renderable | str | None = None
    header_triggers: Sequence[Renderable | None] | str | None = None
    sidebar: Renderable | str | None = None
    css_files: Sequence[str] = field(default_factory=list)

    def on_render(self, request: HttpRequest, ctx: dict[str, Any]) -> str:
        rendered_view = to_html(self.view_content, request, ctx)
        rendered_breadcrumbs = to_html(self.breadcrumbs, request, ctx)

        if isinstance(self.header_triggers, str):
            rendered_triggers = self.header_triggers
        elif isinstance(self.header_triggers, Sequence):
            rendered_triggers = Div(children=self.header_triggers).render(ctx=ctx)
        else:
            rendered_triggers = ""

        view_area = view_frame(default_content=rendered_view).render(request=request)
        breadcrumbs = breadcrumb_frame(default_content=rendered_breadcrumbs).render(
            request=request
        )
        header_triggers = header_triggers_frame(
            default_content=rendered_triggers
        ).render(request=request)

        if self.sidebar is not None:
            sidebar_html = to_html(self.sidebar, request, ctx)
        else:
            sidebar_html = build_sidebar_from_domains(ctx=ctx)

        dashboard_html = format_html(
            DASHBOARD_MAIN_SECTION_HTML,
            breadcrumbs=breadcrumbs,
            view_area=view_area,
            header_triggers=header_triggers,
            sidebar=sidebar_html,
        )

        return Page(content=dashboard_html, css_files=self.css_files).render(
            request=request, ctx=ctx
        )
