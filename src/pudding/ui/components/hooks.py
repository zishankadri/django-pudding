from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from pudding import ui
from pudding.actions.contracts import Action, ActionHook


def modal_hook(**kwargs):
    def show_modal(action: Action, request: HttpRequest, ctx: dict[str, Any]):
        return ui.FrameResponse(
            ui.modal_frame.fill(ui.ActionModal(**kwargs, action=action).render(ctx=ctx))
        )

    return ActionHook(frame=ui.modal_frame, before=show_modal)
