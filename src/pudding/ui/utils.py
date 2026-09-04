from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from django.http import HttpRequest

from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from pudding import ui
from pudding.ui.contracts import AttrValue, HtmlAttrs, Lazy


def resolve_lazy[T](
    value_or_func: Lazy[T],
    ctx: dict[str, Any],
    node: Any = None,
    field_name: str = "",
) -> T:
    if not callable(value_or_func):
        return value_or_func

    return value_or_func(**ctx)  # type: ignore


def resolve_attrs(attrs: dict[str, Any], ctx: dict, node: Any) -> dict[str, Any]:
    resolved = {}
    for key, value in attrs.items():
        resolved[key] = resolve_lazy(value, ctx, node, key)
    return resolved


def attrs_to_html(attrs: dict[str, Any]) -> str:
    """Pure HTML formatter: converts a dict of resolved values into an HTML attribute string."""
    pairs = []
    for k, v in attrs.items():
        if v is True:
            pairs.append(format_html("{}", k))
        elif v is not False and v is not None:
            pairs.append(format_html('{}="{}"', k, v))
    return mark_safe(" ".join(pairs))


def merge_attrs(
    attrs1: HtmlAttrs,
    attrs2: HtmlAttrs,
) -> HtmlAttrs:
    merged: HtmlAttrs = dict(attrs1)

    def _ensure_list(val: AttrValue) -> list[Lazy[str]]:
        return val if isinstance(val, list) else [val]

    for key, value in attrs2.items():
        if key == "class" and key in merged:
            existing = merged[key]

            list_a = _ensure_list(existing)
            list_b = _ensure_list(value)
            combined = list_a + list_b

            if any(callable(i) for i in combined):
                merged[key] = combined
            else:
                merged[key] = " ".join(cast(list[str], combined)).strip()
        else:
            merged[key] = value

    return merged


def build_render_context(
    request: HttpRequest | None,
    ctx: dict[str, Any] | None,
    *,
    extra_ctx: dict[str, Any],
) -> tuple[HttpRequest, dict]:
    assert ctx is not None or request is not None, "Both ctx and request cannot be None"

    combined_ctx = (ctx or {}) | extra_ctx

    if request is not None:
        combined_ctx["request"] = request
    elif "request" not in combined_ctx:
        raise ValueError(
            "A request object must be provided either via the argument or ctx['request']."
        )

    resolved_request = combined_ctx["request"]

    return resolved_request, combined_ctx


def build_sidebar_from_domains(ctx: dict[str, Any]):
    from pudding import domains

    sidebar_items = []
    for slug, domain_class in domains.get_all().items():
        item = ui.Trigger.action(
            "view",
            label=domain_class.label_plural,
            icon=domain_class.icon,
            look=ui.looks.sidebar_item(activation_id=slug),
        ).with_local_context(domain=domain_class)

        sidebar_items.append(item)

    return ui.sidebar(
        ctx=ctx, sidebar_items=sidebar_items, active_id=ctx["domain"].slug
    )


def render_elements(
    elements: Sequence[ui.Renderable],
    ctx: dict[str, Any],
    request: HttpRequest | None = None,
) -> str:
    elements_html = format_html_join(
        "",
        "{}",
        ((element.render(request=request, ctx=ctx),) for element in elements),
    )
    return elements_html
