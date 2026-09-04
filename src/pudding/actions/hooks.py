from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from django.forms.forms import BaseForm
from django.http import HttpRequest
from django.utils.functional import Promise

from pudding import ui
from pudding.ui.contracts import UNSET, Lazy, UnsetType
from pudding.ui.primitives import Trigger as CoreTrigger

from .contracts import Action, ActionHook


def Modal(
    icon: str | None | UnsetType = UNSET,
    icon_color: Lazy[Literal["primary", "danger", "warning", "success", "gray", "info"]]
    | None = None,
    eyebrow: str | Promise | None = None,
    title: str | Promise | None = None,
    subtitle: str | Promise | None = None,
    form: BaseForm | None = None,
    body: Lazy[str] | None = None,
    button: Callable[[CoreTrigger], CoreTrigger] = lambda btn: btn,
    local_context: dict[str, Any] | None = None,
):

    def show_modal(action: Action, request: HttpRequest, ctx: dict[str, Any]):
        return ui.FrameResponse(
            ui.modal_frame.fill(
                ui.ActionModal(
                    action=action,
                    icon=icon,
                    icon_color=icon_color,
                    eyebrow=eyebrow,
                    title=title,
                    subtitle=subtitle,
                    form=form,
                    body=body,
                    button=button,
                    local_context=local_context or {},
                ).render(ctx=ctx)
            )
        )

    return ActionHook(frame=ui.modal_frame, before=show_modal)
