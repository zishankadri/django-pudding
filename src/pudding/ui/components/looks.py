from collections.abc import Iterable
from typing import Literal

from django.utils.html import format_html
from django.utils.safestring import mark_safe

from pudding.ui.contracts import LookType, Size, TriggerProps
from pudding.ui.utils import attrs_to_html

Variant = Literal["solid", "ghost", "outline", "danger", "ghost-danger"]

VARIANT_CLASS_MAP: dict[Variant, str] = {
    "solid": "btn-solid",
    "ghost": "btn-ghost",
    "outline": "btn-outline",
    "danger": "btn-danger",
    "ghost-danger": "btn-ghost-danger",
}
SIZE_CLASS_MAP: dict[Size, str] = {
    "normal": "btn-size-normal",
    "sm": "btn-size-sm",
    "lg": "btn-size-lg",
    "icon": "btn-size-icon",
    "icon-sm": "btn-size-icon-sm",
    "icon-md": "btn-size-icon-md",
    "icon-lg": "btn-size-icon-lg",
}
LOADING_SPINNER_HTML = mark_safe(
    '<span class="loading-spinner-for-trigger hidden absolute flex justify-center items-center inset-0 rounded-[inherit]">'
    '<i data-lucide="loader-circle" class="animate-spin"></i>'
    "</span>"
)


def _render_trigger_element(
    props: TriggerProps, base_class: str, extra_classes: Iterable[str] | None = None
) -> str:
    """Core HTML renderer shared across all UI trigger factories."""
    classes = [base_class]

    existing_class = props.attrs.pop("class", "")
    if isinstance(existing_class, list):
        classes.extend(existing_class)
    elif existing_class:
        classes.append(str(existing_class))

    if extra_classes:
        classes.extend(extra_classes)

    if props.loading:
        classes.append("relative")
        props.attrs.setdefault("hx-disabled-elt", "this")

    props.attrs["class"] = " ".join(dict.fromkeys(classes)).strip()

    icon_html = (
        format_html('<i data-lucide="{}"></i>', props.icon) if props.icon else ""
    )
    loading_html = LOADING_SPINNER_HTML if props.loading else ""
    attrs_html = attrs_to_html(props.attrs)

    return format_html(
        "<{tag} {attrs}> {icon} {label} {loading_indicator} </{tag}>",
        tag=props.tag,
        attrs=attrs_html,
        icon=icon_html,
        label=props.label,
        loading_indicator=loading_html,
    )


class Looks:
    """Namespace container used to keep IDE autocompletion clean."""

    def button(
        self,
        variant: Variant,
    ) -> LookType:
        variant_class = VARIANT_CLASS_MAP.get(variant)

        def button_look(props: TriggerProps) -> str:
            size_class = SIZE_CLASS_MAP.get(props.size)
            extra_classes = [c for c in (variant_class, size_class) if c]

            return _render_trigger_element(
                props, base_class="btn", extra_classes=extra_classes
            )

        return button_look

    def dropdown_item(self, variant: Literal["normal", "opener", "danger"] = "normal"):
        def dropdown_item_look(props: TriggerProps) -> str:
            return _render_trigger_element(props, base_class="dropdown-item")

        return dropdown_item_look

    def breadcrumb(self, active: bool = False):
        def breadcrumb_look(props: TriggerProps) -> str:
            extra = ["active"] if active else None
            return _render_trigger_element(
                props,
                base_class="breadcrumb-item",
                extra_classes=extra,
            )

        return breadcrumb_look

    def sidebar_item(self, active: bool = False, activation_id: str | None = None):
        def sidebar_item_look(props: TriggerProps) -> str:
            extra = ["active"] if active else None
            if activation_id:
                props = props(
                    attrs=props.attrs
                    | {":class": f"{{'active': activeId === '{activation_id}' }}"}
                )
            return _render_trigger_element(
                props, base_class="sidebar-item", extra_classes=extra
            )

        return sidebar_item_look


looks = Looks()
