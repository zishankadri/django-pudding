from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, override

from django.db import models
from django.http import HttpRequest, HttpResponse

from pudding import actions, ui
from pudding.actions.contracts import Action
from pudding.ui.components import DashboardPage
from pudding.ui.utils import render_elements


class View(Action):
    def __init__(
        self,
        *,
        slug: str = "view",
        icon: str | None = None,
        header_actions: list[ui.Trigger] | None = None,
        view: ui.Renderable | None = None,
        modal_frame: ui.Frame = ui.modal_frame,
        view_frame: ui.Frame = ui.view_frame,
        css_files: Sequence[str] | None = None,
        permission: Callable[[HttpRequest], bool] = lambda req: True,
    ) -> None:
        self.slug = slug
        self.icon = icon

        self.header_actions = header_actions or []
        self.view = view
        self.modal_frame = ui.modal_frame
        self.view_frame = ui.view_frame

        self.permission = permission

        self.css_files = css_files or []

    @override
    def handle(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        domain = ctx["domain"]

        model: type[models.Model] | None = getattr(domain, "model", None)
        if not model:
            raise TypeError(
                f"Action '{self.__class__.__name__}' requires context 'domain' to have model."
            )

        queryset = model._default_manager.all()

        ctx |= {"queryset": queryset}

        view_content = self.view.render(ctx=ctx) if self.view else ""
        breadcrumbs = ui.Breadcrumbs(
            children=(
                ui.BreadcrumbLabel(
                    label=domain.label_plural,
                    icon=domain.icon,
                    active=True,
                    attrs={"class": "font-medium"},
                ),
            ),
        ).render(ctx=ctx)
        header_actions = render_elements(self.header_actions, ctx=ctx)

        if actions.is_htmx(request):
            return ui.FrameResponse(
                ui.view_frame.fill(view_content),
                ui.breadcrumb_frame.fill(breadcrumbs),
                ui.header_triggers_frame.fill(header_actions),
                push_action_url={"action_slug": self.slug, "domain_slug": domain.slug},
                trigger_events=[{"set-active-sidebar-item": {"slug": domain.slug}}],
            )

        body = DashboardPage(
            view_content=self.view,
            breadcrumbs=breadcrumbs,
            header_triggers=self.header_actions,
            css_files=self.css_files,
        ).render(request=request, ctx=ctx)

        return HttpResponse(content=body)
