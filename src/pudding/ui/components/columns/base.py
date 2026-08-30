from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from django.db import models
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.functional import Promise

from pudding.ui.utils import build_render_context


@dataclass(slots=True)
class Column:
    """A table column."""

    label: str | Promise
    renderer: Callable[[models.Model], Any]
    ordering_field: str | None = None

    local_context: dict[str, Any] = field(default_factory=dict)

    def render(self, request: HttpRequest, ctx: dict[str, Any]) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        row = ctx["row"]
        value = self.renderer(row)

        return render_to_string(
            "pudding/components/table/table_cell.html",
            context={"value": value},
            request=request,
        )
