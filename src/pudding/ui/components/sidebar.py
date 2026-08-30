from typing import Any

from django.template.loader import render_to_string
from django.utils.html import format_html_join


def sidebar(
    ctx: dict[str, Any],
    sidebar_items,
    active_id: str,
    header_content: str = "",
    bottom_items: str = "",
):
    sidebar_items = format_html_join(
        "",
        "{}",
        ((action.render(ctx=ctx),) for action in sidebar_items),
    )

    return render_to_string(
        "pudding/components/sidebar.html",
        request=ctx["request"],
        context={
            "active_id": active_id,
            "header_content": header_content,
            "sidebar_items": sidebar_items,
            "bottom_items": bottom_items,
        },
    )
