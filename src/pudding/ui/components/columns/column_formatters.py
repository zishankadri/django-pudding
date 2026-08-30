from datetime import date, datetime, time
from typing import Any

from django.db.models.fields.files import ImageFieldFile
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.html import format_html
from django.utils.safestring import mark_safe


def default_formatter(value: Any) -> Any:
    match value:
        case ImageFieldFile():
            value = image_formatter(value)

        case datetime():  # Must come before date!
            value = formats.date_format(value, "DATETIME_FORMAT")

        case date():
            value = formats.date_format(value, "DATE_FORMAT")

        case time():
            value = formats.time_format(value, "TIME_FORMAT")

    value = value if value is not None else "-"
    return value


def sparkline_formatter(
    values,
    stroke: str = "var(--color-accent)",
    stroke_width: int = 1,
) -> str:
    if not values:
        return ""

    width = 80
    height = 32

    max_val = max(values) or 1
    step_x = width / (len(values) - 1)

    points = [
        (i * step_x, height - (v / max_val * height)) for i, v in enumerate(values)
    ]

    # Quadratic curve path
    d = f"M {points[0][0]} {points[0][1]} "
    for i in range(1, len(points) - 1):
        x_mid = (points[i][0] + points[i + 1][0]) / 2
        y_mid = (points[i][1] + points[i + 1][1]) / 2
        d += f"Q {points[i][0]} {points[i][1]}, {x_mid} {y_mid} "
    d += f"T {points[-1][0]} {points[-1][1]}"

    # Shading path
    fill_path = d + f" L {points[-1][0]} {height} L {points[0][0]} {height} Z"

    return format_html(
        """
        <svg width="{}" height="{}" viewBox="0 0 {} {}">
            <defs>
                <linearGradient id="bottomShade" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="20%" stop-color="{}" stop-opacity="0.25" />
                    <stop offset="50%" stop-color="{}" stop-opacity="0.15" />
                    <stop offset="100%" stop-color="{}" stop-opacity="0" />
                </linearGradient>
            </defs>
            <path d="{}" fill="url(#bottomShade)" stroke="none" />
            <path d="{}" fill="none" stroke="{}" stroke-width="{}" />
        </svg>
        """,
        width,
        height,
        width,
        height,
        stroke,
        stroke,
        stroke,
        fill_path,
        d,
        stroke,
        stroke_width,
    )


def profile_formatter(
    title_text: str,
    subtitle_text: str | None = None,
    image_url: str | None = None,
) -> str:
    context = {
        "title_text": title_text,
        "subtitle_text": subtitle_text,
        "image_url": image_url,
    }
    return render_to_string("pudding/table_columns/profile.html", context)


def image_formatter(
    value,
    extra_classes="h-10 w-10 rounded-md",
) -> str:
    if value and hasattr(value, "url"):
        return format_html(
            '<img src="{}" alt="Image" class="{} object-cover">',
            value.url,
            extra_classes,
        )

    return mark_safe(
        '<span class="text-foreground-tertiary" aria-label="No image available">-</span>'
    )
