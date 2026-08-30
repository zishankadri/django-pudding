from collections.abc import Callable
from typing import Any

from django.db import models
from django.utils.functional import Promise

from .base import Column
from .column_formatters import default_formatter
from .column_renderers import make_profile_renderer


def make_field_renderer(field_name: str) -> Callable[[models.Model], Any]:
    def field_renderer(row: models.Model) -> Any:
        attr = getattr(row, field_name)
        value = attr() if callable(attr) else attr
        return default_formatter(value)

    field_renderer.__name__ = field_name
    return field_renderer


def FieldColumn(
    field: str,
    label: str | Promise | None = None,
    ordering_field: str | None = None,
) -> Column:
    """Factory for rendering a model field, property, or method by attribute name."""
    normalized_label = label or field.replace("_", " ").replace("-", " ").capitalize()

    return Column(
        label=normalized_label,
        renderer=make_field_renderer(field),
        ordering_field=ordering_field or field,
    )


def ProfileColumn(
    title_field: str,
    label: str | Promise | None = None,
    subtitle_field: str | None = None,
    image_field: str | None = None,
) -> Column:
    """Build a column for rendering profiles by combining multiple model fields."""
    return Column(
        label=label or title_field.replace("-", " ").replace("_", " "),
        renderer=make_profile_renderer(
            title_field=title_field,
            subtitle_field=subtitle_field,
            image_field=image_field,
        ),
    )
