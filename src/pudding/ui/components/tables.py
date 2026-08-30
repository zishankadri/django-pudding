from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from pudding import ui
from pudding.ui.utils import build_render_context


def apply_search(
    queryset: QuerySet, request: HttpRequest, model, search_fields
) -> QuerySet:
    """Applies search filters based on GET parameters and model configuration."""
    query = request.GET.get("q", "").strip()
    if not query:
        return queryset

    # Sanitize wildcards to prevent ReDoS/Database heavy scans
    sanitized_query = re.sub(r"[%_]", "", query)
    if not sanitized_query:
        return queryset

    fields = search_fields or [
        f.name
        for f in model._meta.get_fields()
        if getattr(f, "concrete", False)
        and getattr(f, "get_internal_type", lambda: "")()
        in {"CharField", "TextField", "EmailField", "SlugField", "UUIDField"}
    ]

    filters = Q()
    for f in fields:
        filters |= Q(**{f"{f}__icontains": sanitized_query})

    if sanitized_query.isdigit() and getattr(model._meta, "pk", None):
        filters |= Q(**{model._meta.pk.name: int(sanitized_query)})

    return queryset.filter(filters)


def apply_filtering(queryset: QuerySet, request: HttpRequest, model) -> QuerySet:
    """Applies individual column filters based on GET parameters."""
    filter_field = request.GET.get("filter_field")
    filter_operation = request.GET.get("filter_operation")
    filter_value = request.GET.get("filter_value", "").strip()

    if not (filter_field and filter_operation and filter_value):
        return queryset

    concrete_fields = {
        f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)
    }

    lookups = {
        "eq": "",
        "contains": "__icontains",
        "startswith": "__istartswith",
        "endswith": "__iendswith",
        "gt": "__gt",
        "gte": "__gte",
        "lt": "__lt",
        "lte": "__lte",
    }

    if filter_field in concrete_fields and (
        filter_operation in lookups or filter_operation == "neq"
    ):
        kw = {f"{filter_field}{lookups.get(filter_operation, '')}": filter_value}
        if filter_operation == "neq":
            return queryset.exclude(**kw)
        return queryset.filter(**kw)

    return queryset


def apply_ordering(queryset: QuerySet, order_by) -> QuerySet:
    """Applies ordering rules from the model configuration."""
    if order := order_by:
        return queryset.order_by(*order)
    return queryset


@dataclass
class Table:
    model: type[models.Model]

    bulk_actions: list | None = None
    row_actions: list | None = None
    row_detail_template: str | None = None

    columns: Sequence[ui.Column | str] = field(default_factory=list)
    order_by: str | None = None
    search_fields: list[str] | None = None
    paginated_by: int = 25
    paginator_class: type[Paginator] = Paginator

    local_ctx: dict = field(default_factory=dict)

    def __post_init__(self):
        row_columns = self.columns or [
            ui.FieldColumn(field)
            for field in [field.name for field in self.model._meta.fields]
        ]

        self.normalized_columns = [
            self._normalize_column(column) for column in row_columns
        ]

    def render(
        self,
        request: HttpRequest | None = None,
        ctx: dict[str, Any] | None = None,
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_ctx)

        queryset = ctx["queryset"]
        model = ctx["domain"].model

        queryset = apply_search(queryset, request, model, self.search_fields)
        queryset = apply_filtering(queryset, request, model)
        queryset = apply_ordering(queryset, self.order_by)

        try:
            page_num = int(request.GET.get("page", 1))
        except ValueError:
            page_num = 1

        paginator = Paginator(queryset, self.paginated_by)
        page_obj = paginator.get_page(page_num)
        ctx = ctx | {
            "queryset": page_obj,
            "paginator": paginator,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
        }

        bulk_actions = (
            self.render_actions(self.bulk_actions, request=request, ctx=ctx)
            if self.bulk_actions
            else None
        )

        all_rows_html = [
            TableRow(
                columns=self.normalized_columns,
                row_actions=self.row_actions,
                row_detail_template=self.row_detail_template,
            ).render(request, ctx=ctx | {"row": row})
            for row in page_obj
        ]
        combined_rows_html = mark_safe("".join(all_rows_html))
        context = ctx | {
            "bulk_actions": bulk_actions,
            "show_actions_column": bool(self.row_actions),
            "columns": self.normalized_columns,
            "rows": combined_rows_html,
            "filter_fields": [
                f.name
                for f in self.model._meta.get_fields()
                if getattr(f, "concrete", False)
            ],
            "empty_table_actions": ui.Trigger.action(
                "add",
                label=f"Add {ctx['domain'].slug}",
                icon="plus",
                look=ui.looks.button(variant="outline"),
                size="sm",
            )(**ui.view_frame.loading_mod).render(ctx=ctx),
        }
        response = render_to_string(
            "pudding/components/table/table.html",
            request=request,
            context=context,
        )
        return response

    def render_actions(
        self, actions: list[ui.Trigger], request: HttpRequest | None, ctx: dict
    ):
        actions_html = format_html_join(
            "",
            "{}",
            ((action.render(request=request, ctx=ctx),) for action in actions),
        )
        return actions_html

    def _normalize_column(self, column_or_str: ui.Column | str) -> ui.Column:
        if isinstance(column_or_str, ui.Column):
            return column_or_str

        if isinstance(column_or_str, str):
            try:
                model_field = self.model._meta.get_field(column_or_str)
                if verbose_name := getattr(model_field, "verbose_name", None):
                    label = verbose_name.capitalize()
            except FieldDoesNotExist:
                label = None

            return ui.FieldColumn(column_or_str, label=label)

        raise TypeError(
            f"Invalid list_display item: {column_or_str}. Expected Column instance or str."
        )


@dataclass
class TableRow:
    columns: list
    row_actions: list | None
    row_detail_template: str | None

    local_context: dict[str, Any] = field(default_factory=dict)

    def render(
        self, request: HttpRequest | None = None, ctx: dict[str, Any] | None = None
    ) -> str:
        request, ctx = build_render_context(request, ctx, extra_ctx=self.local_context)

        row_ctx = {
            "request": request,
            "domain_slug": ctx["domain"].slug,
            "row": ctx["row"],
        }

        if self.row_actions:
            actions_html = format_html_join(
                "",
                "{}",
                (
                    (action.render(request=request, ctx=ctx),)
                    for action in self.row_actions
                ),
            )
        else:
            actions_html = mark_safe("")

        columns_html = format_html_join(
            "",
            "{}",
            ((column.render(ctx["row"], row_ctx),) for column in self.columns),
        )

        row_context = {
            "row": ctx["row"],
            "columns": columns_html,
            "row_actions": actions_html,
        }

        return render_to_string(
            "pudding/components/table/table_row.html",
            request=request,
            context=row_context,
        )
