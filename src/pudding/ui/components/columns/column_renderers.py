from collections.abc import Callable
from typing import Any

from django.db import models

from .column_formatters import (
    image_formatter,
    profile_formatter,
    sparkline_formatter,
)

type ColumnRenderer = Callable[[models.Model], str]
type Formatter = Callable[..., str]


# Utility function
def resolve_attr(obj, path):
    current = obj
    for part in path.split("."):
        if not hasattr(current, part):
            model_name = current.__class__.__name__
            raise AttributeError(
                f"Invalid field path '{path}' for {model_name}: missing '{part}'"
            )
        current = getattr(current, part)
    return current


def make_image_renderer(field: str, **formatter_options) -> ColumnRenderer:
    """
    Create a ColumnRenderer function for displaying an object's image field.

    The returned function renders an <img> tag when the field has a URL,
    otherwise it renders a placeholder.
    """

    def render(obj) -> str:
        value = resolve_attr(obj, field)

        return image_formatter(value, **formatter_options)

    return render


def make_price_renderer(field, symbol="$") -> ColumnRenderer:
    def render(obj):
        value = resolve_attr(obj, field)
        return f"{symbol}{value:,.2f}"

    return render


def make_sparkline_renderer(
    value_function: str | Callable,
    **formatter_options,
) -> ColumnRenderer:
    def render(obj: Any) -> str:
        values: Any = None

        if callable(value_function):
            values = value_function(obj)
        elif isinstance(value_function, str) and value_function:
            try:
                resolved = resolve_attr(obj, value_function)
            except AttributeError as exc:
                raise AttributeError(
                    f"Failed to resolve path '{value_function}' on {obj.__class__.__name__}"
                ) from exc

            if callable(resolved):
                try:
                    values = resolved()
                except TypeError:
                    # Fallback: maybe it's an unbound method requiring the obj
                    values = resolved(obj)
            else:
                values = resolved

        if values is None:
            values = []

        if not isinstance(values, (list, tuple)):
            try:
                values = list(values)
            except TypeError:
                raise ValueError(
                    f"Resolved value at '{value_function}' is not iterable: {values!r}"
                )

        return sparkline_formatter(values=values, **formatter_options)

    return render


def make_profile_renderer(
    title_field: str,
    subtitle_field: str | None = None,
    image_field: str | None = None,
    **formatter_options,
) -> ColumnRenderer:
    def render(obj) -> str:
        title_text = resolve_attr(obj, title_field) or ""
        subtitle_text = resolve_attr(obj, subtitle_field) if subtitle_field else None
        image_obj = resolve_attr(obj, image_field) if image_field else None
        image_url = getattr(image_obj, "url", None)

        return profile_formatter(
            title_text=title_text,
            subtitle_text=subtitle_text,
            image_url=image_url,
            **formatter_options,
        )

    render.__name__ = title_field

    return render
