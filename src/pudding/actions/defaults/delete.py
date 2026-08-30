from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from pudding import ui
from pudding.actions.base import InteractiveAction
from pudding.ui import Trigger
from pudding.ui.primitives import Frame


class Delete(InteractiveAction):
    def __init__(
        self,
        slug: str = "delete",
        icon: str | None = "trash-2",
        modal_frame: Frame = ui.modal_frame,
        *args,
        **kwargs,
    ):
        super().__init__(*args, slug=slug, icon=icon, **kwargs)

        self.modal_frame = modal_frame

        self.trigger = Trigger.action(
            self, look=ui.looks.button(variant="ghost-danger")
        )(**self.modal_frame.loading_mod)

    def before(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        domain = ctx["domain"]
        model = domain.model

        opts = model._meta
        queryset = ctx["queryset"]
        count = queryset.count()
        if count == 0:
            raise Http404(_("No items selected for deletion."))

        if count == 1:
            title = str(queryset.first())
        else:
            title = ngettext(
                "{count} {model_name}", "{count} {model_name_plural}", count
            ).format(
                count=count,
                model_name=opts.verbose_name,
                model_name_plural=opts.verbose_name_plural,
            )
        return ui.FrameResponse(
            self.modal_frame.fill(
                ui.ActionModal(
                    action=self,
                    eyebrow=_("Delete"),
                    title=title,
                    button=lambda btn: btn(look=ui.looks.button(variant="danger")),
                    icon_color="danger",
                ).render(ctx=ctx)
            )
        )

    def execute(self, request: HttpRequest, ctx: dict[str, Any]) -> HttpResponse:
        model = ctx["domain"].model

        opts = model._meta
        queryset = ctx["queryset"]
        count = queryset.count()
        if count == 0:
            raise Http404(_("No items selected for deletion."))

        queryset.delete()

        success_message = ngettext(
            "Deleted {count} {model_name}.",
            "Deleted {count} {model_name_plural}.",
            count,
        ).format(
            count=count,
            model_name=opts.verbose_name,
            model_name_plural=opts.verbose_name_plural,
        )

        messages.success(request, success_message)
        response = HttpResponse()
        response["HX-Redirect"] = reverse(
            "pudding:run_action",
            kwargs={
                "domain_slug": ctx["domain"].slug,
                "action_slug": "view",
            },
        )
        return response
