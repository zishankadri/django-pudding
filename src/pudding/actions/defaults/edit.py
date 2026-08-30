from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pudding import ui
from pudding.actions.base import InteractiveAction
from pudding.actions.defaults.utils import get_form_class
from pudding.ui import Trigger


class Edit(InteractiveAction):
    def __init__(
        self,
        slug: str = "edit",
        icon: str | None = "pen-line",
        fields: list[str] | None = None,
        exclude: list[str] | None = None,
        dock_actions: list[ui.Trigger] | None = None,
        modal_frame: ui.Frame = ui.modal_frame,
        **kwargs,
    ):
        super().__init__(slug=slug, icon=icon, **kwargs)

        self.fields = fields
        self.exclude = exclude
        self.dock_actions: list[ui.Trigger] = dock_actions or []
        self.modal_frame = modal_frame

        self.trigger = Trigger.action(self, size="icon-sm")(
            **self.modal_frame.loading_mod
        )

    def before(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        domain = ctx["domain"]
        model = domain.model

        FormClass = get_form_class(model=model)

        instance = ctx["queryset"][0] if ctx["queryset"] else None
        form = FormClass(instance=instance)

        return ui.FrameResponse(
            self.modal_frame.fill(
                ui.ActionModal(action=self, form=form, title=f"Edit {instance}").render(
                    ctx=ctx
                )
            )
        )

    def execute(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        domain = ctx["domain"]
        model = domain.model

        FormClass = get_form_class(model=model)

        instance = ctx["queryset"][0] if ctx["queryset"] else None
        form = FormClass(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _("{name} edited successfully!").format(
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
            return ui.FrameResponse(
                self.modal_frame.fill(
                    ui.ActionModal(
                        action=self, form=form, icon=None, title=f"Edit {instance}"
                    ).render(ctx=ctx)
                )
            )
