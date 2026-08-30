from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from django.utils.functional import Promise

from pudding.ui.components.looks import looks
from pudding.ui.components.triggers import Trigger
from pudding.ui.primitives import Trigger as CoreTrigger

if TYPE_CHECKING:
    from django.forms import BaseForm
    from django.http import HttpRequest

    from pudding.actions.contracts import Action

from django.template.loader import render_to_string
from django.utils.html import conditional_escape, format_html
from django.utils.translation import gettext_lazy as _

from pudding.actions.contracts import Action
from pudding.ui.contracts import UNSET, Lazy, UnsetType
from pudding.ui.utils import build_render_context, resolve_lazy

ICON_COLOR_MAP = {
    "primary": "bg-neutral-500/8 border-border-secondary",
    "danger": "text-error bg-error/10 border-error/20",
    "gray": "bg-neutral-500/8 border-border-secondary",
    "info": "text-blue-500 bg-blue-500/10 border-blue-500/20",
    "warning": "text-orange-500 bg-orange-500/8 border-orange-500/20",
    "success": "text-green-500 bg-green-500/8 border-green-500/20",
}


@dataclass
class Modal:
    icon: str | None | UnsetType = UNSET
    icon_color: (
        Lazy[Literal["primary", "danger", "warning", "success", "gray", "info"]] | None
    ) = None

    eyebrow: str | Promise | None = None
    title: str | Promise | None = None
    subtitle: str | Promise | None = None

    body: Lazy[str] | None = None
    footer: Lazy[str] | None = None

    local_context: dict[str, Any] = field(default_factory=dict)

    def render(
        self,
        request: HttpRequest | None = None,
        ctx: dict[str, Any] | None = None,
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        resolved_icon_color = self.resolve("icon_color", ctx) or "primary"
        icon_color_classes = ICON_COLOR_MAP.get(resolved_icon_color)
        icon_size_css = (
            "text-xl h-11" if self.eyebrow or self.subtitle else "text-sm h-8"
        )
        return render_to_string(
            "pudding/components/overlays/modal.html",
            context={
                "icon": self.icon,
                "icon_size_css": icon_size_css,
                "icon_color_classes": icon_color_classes,
                "eyebrow": self.eyebrow,
                "title": self.title,
                "sub_title": self.subtitle,
                "modal_body": self.resolve("body", ctx) or "",
                "footer": self.resolve("footer", ctx) or "",
            },
            request=request,
        )

    def resolve(self, field_name: str, ctx: dict[str, Any]):
        value_or_func = getattr(self, field_name)
        return resolve_lazy(
            value_or_func=value_or_func, ctx=ctx, node=self, field_name=field_name
        )


@dataclass(frozen=True)
class ActionModal:
    action: Action

    icon: str | None | UnsetType = UNSET
    icon_color: (
        Lazy[Literal["primary", "danger", "warning", "success", "gray", "info"]] | None
    ) = None

    eyebrow: str | Promise | None = None
    title: str | Promise | None = None
    subtitle: str | Promise | None = None

    form: BaseForm | None = None
    body: Lazy[str] | None = None

    button: Callable[[CoreTrigger], CoreTrigger] = lambda btn: btn

    local_context: dict[str, Any] = field(default_factory=dict)

    def render(
        self,
        *,
        request: HttpRequest | None = None,
        ctx: dict[str, Any] | None = None,
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        action = self.action
        icon = self.icon if self.icon is not UNSET else action.icon
        display_title = self.title or _("Execute %(slug)s") % {"slug": action.slug}
        modal_body = conditional_escape(self.resolve("body", ctx) or "")
        pks = request.POST.getlist("pks[]") or request.GET.getlist("pks[]")

        action_button = Trigger.action(
            action_or_slug=action.slug,
            icon=icon,
            label=_(action.slug.replace("_", " ").capitalize()),
            method="post",
            look=looks.button(variant="solid"),
        )

        if self.form is not None:
            form_id = "modal-form"
            validity_guard = (
                f"const f = document.getElementById('{form_id}');"
                " if (!f.checkValidity()) { event.preventDefault(); f.reportValidity(); }"
            )
            action_button = action_button(
                attrs={
                    "form": form_id,
                    "hx-on::before-request": validity_guard,
                    "hx-encoding": "multipart/form-data",
                }
            )
            modal_body += render_to_string(
                "pudding/components/form.html",
                {"form": self.form, "form_id": form_id},
                request=request,
            )
        cancel_button = Trigger(
            tag="button",
            label=_("Cancel"),
            attrs={
                "@click": "$refs.puddingModal.close()",
                "class": "bg-transparent hover:bg-neutral-500/10",
            },
            look=looks.button(variant="outline"),
        ).render(ctx=ctx)
        action_button_html = self.button(action_button).render(ctx=ctx)

        footer = format_html(
            '<div hx-vals="{ids}" class="flex gap-2 items-center"> {cancel}{action}</div>',
            ids=json.dumps({"pks[]": pks}),
            cancel=cancel_button,
            action=action_button_html,
        )
        return Modal(
            icon=icon,
            icon_color=self.icon_color,
            eyebrow=self.eyebrow,
            title=display_title,
            subtitle=self.subtitle,
            body=format_html(
                '<div class="mt-8">{modal_body}</div>', modal_body=modal_body
            ),
            footer=footer,
        ).render(ctx=ctx)

    def resolve(self, field_name: str, ctx: dict[str, Any]):
        value_or_func = getattr(self, field_name)
        return resolve_lazy(
            value_or_func=value_or_func, ctx=ctx, node=self, field_name=field_name
        )
