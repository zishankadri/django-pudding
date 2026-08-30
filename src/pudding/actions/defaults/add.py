from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from pudding import actions, ui
from pudding.actions.base import InteractiveAction
from pudding.actions.defaults.utils import (
    get_form_class,
)


def get_content(self, form, request, ctx):
    submit_btn = ui.Trigger.action(
        self.slug,
        label=_("Save"),
        method="post",
        look=ui.looks.button(variant="solid"),
    )

    form_id = "modal-form"
    validity_guard = (
        f"const f = document.getElementById('{form_id}');"
        " if (!f.checkValidity()) { event.preventDefault(); f.reportValidity(); }"
    )
    submit_btn = submit_btn(
        attrs={
            "form": form_id,
            "hx-on::before-request": validity_guard,
            "hx-encoding": "multipart/form-data",
        }
    )
    form_html = render_to_string(
        "pudding/components/form.html",
        {"form": form, "form_id": form_id},
        request=request,
    )

    submit_btn = submit_btn.render(ctx=ctx)

    return form_html, submit_btn


class Add(InteractiveAction):
    def __init__(
        self,
        slug: str = "add",
        icon: str | None = "plus",
        modal_frame: ui.Frame = ui.modal_frame,
        view_frame: ui.Frame = ui.view_frame,
        css_files: Sequence[str] | None = None,
        **kwargs,
    ):
        super().__init__(slug=slug, icon=icon, **kwargs)

        self.modal_frame = modal_frame
        self.view_frame = view_frame

        self.trigger = ui.Trigger.action(self, look=ui.looks.button(variant="outline"))(
            **self.view_frame.loading_mod
        )

        self.css_files = css_files or []

    def before(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        domain = ctx["domain"]
        model = domain.model

        pks = request.POST.getlist("pks[]") or request.GET.getlist("pks[]")

        FormClass = get_form_class(model=model)

        base_label = _(model._meta.verbose_name_plural).title()
        breadcrumbs = ui.Breadcrumbs(
            children=[
                ui.Trigger.action("view", label=base_label, icon=domain.icon),
                ui.BreadcrumbLabel(label=_("Add"), icon="plus"),
            ]
        ).render(request=request, ctx=ctx)

        form_html, submit_btn = get_content(
            self, form=FormClass(), request=request, ctx=ctx
        )
        header_triggers = format_html(
            '<div hx-vals="{ids}" class="flex gap-2 items-center"> {submit}</div>',
            ids=json.dumps({"pks[]": pks}),
            submit=submit_btn,
        )

        if actions.is_htmx(request):
            return ui.FrameResponse(
                ui.view_frame.fill(form_html),
                ui.breadcrumb_frame.fill(breadcrumbs),
                ui.header_triggers_frame.fill(header_triggers),
                push_action_url={"action_slug": "add", "domain_slug": domain.slug},
            )

        body = ui.DashboardPage(
            view_content=form_html,
            breadcrumbs=breadcrumbs,
            header_triggers=header_triggers,
            css_files=self.css_files,
        ).render(request=request, ctx=ctx)

        return HttpResponse(content=body)

    def execute(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        domain = ctx["domain"]
        model = domain.model

        FormClass = get_form_class(model=model)

        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _("{name} created successfully!").format(
                    name=_(model._meta.verbose_name.capitalize())
                ),
            )
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse(
                "pudding:run_action",
                kwargs={
                    "domain_slug": domain.slug,
                    "action_slug": "view",
                },
            )
            return response
        else:
            form_html, submit_btn = get_content(
                self, form=form, request=request, ctx=ctx
            )
            return ui.FrameResponse(
                ui.view_frame.fill(form_html), ui.header_triggers_frame.fill(submit_btn)
            )
