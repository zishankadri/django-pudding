from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest

    from pudding import domains
    from pudding.actions import Action

from django.urls import reverse
from django.utils.functional import Promise

from pudding.ui.components.looks import looks
from pudding.ui.contracts import Lazy, LookType, Renderable, Size
from pudding.ui.primitives.triggers import ActionTrigger, Group, Shell
from pudding.ui.primitives.triggers import Trigger as CoreTrigger
from pudding.ui.utils import merge_attrs

type Handler = Callable[[domains.Domain, HttpRequest, QuerySet], Any]
type HtmlAttrs = dict[str, Any]
type GetURL = Callable[..., str]


@runtime_checkable
class HasTrigger(Renderable, Protocol):
    @property
    def trigger(self) -> CoreTrigger: ...
    def __call__(self, **kwargs) -> Self: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Trigger(CoreTrigger):
    """
    Opinionated Trigger facade providing developer-friendly factory methods.
    """

    look: LookType = field(default_factory=lambda: looks.button(variant="ghost"))

    @classmethod
    def action(
        cls,
        action_or_slug: Action | str,
        label: str | Promise = "",
        method: str = "get",
        attrs: HtmlAttrs | None = None,
        look: LookType | None = None,
        size: Lazy[Size] = "normal",
        **kwargs,
    ) -> ActionTrigger:
        attrs = attrs or {}

        if hasattr(action_or_slug, "slug"):
            action_slug = action_or_slug.slug
            icon = getattr(action_or_slug, "icon", None)
            if icon and "icon" not in kwargs:
                kwargs["icon"] = icon
        elif isinstance(action_or_slug, str):
            action_slug = action_or_slug
        else:
            raise TypeError(
                f"Expected an Action instance or string, got {type(action_or_slug).__name__}"
            )

        if not label:
            label = action_slug.replace("_", " ").replace("-", " ").capitalize()

        action_attrs: HtmlAttrs = {
            "type": "button",
            f"hx-{method}": lambda request, domain, **kwargs: get_action_url(
                request, domain.slug, action_slug
            ),
        }

        return ActionTrigger(
            action_slug=action_slug,
            tag="button",
            label=label if label else "",
            attrs=merge_attrs(action_attrs, attrs),
            size="icon" if not bool(label) else size,
            look=look or looks.button(variant="ghost"),
            **kwargs,
        )

    @classmethod
    def link(cls, get_url: Callable[..., str], **kwargs: Any) -> CoreTrigger:
        return Trigger(
            tag="a",
            attrs={"href": get_url},
            **kwargs,
        )


def get_action_url(request, domain_slug, action_slug):
    cache = getattr(request, "_url_cache", None)
    if cache is None:
        cache = {}
        request._url_cache = cache

    # Note: Tenant, language, and host info are implicit in the 'request' object.
    # Since this cache is per-request, we don't need to include them in the key.
    cache_key = (domain_slug, action_slug)
    if cache_key not in cache:
        cache[cache_key] = reverse(
            "pudding:run_action",
            kwargs={
                "domain_slug": domain_slug,
                "action_slug": action_slug,
            },
        )
    return cache[cache_key]


disclosure: CoreTrigger = Trigger(
    tag="button",
    icon="ellipsis-vertical",
    size="icon",
    attrs={
        "@click": "isOpen = ! isOpen",
        "aria-haspopup": "true",
        "@keydown.space.prevent": "isOpen = true",
        "@keydown.enter.prevent": "isOpen = true",
        "@keydown.down.prevent": "isOpen = true",
        "x-bind:aria-expanded": "isOpen",
    },
)


def Dropdown(
    *children: CoreTrigger,
    trigger: Callable[[CoreTrigger], CoreTrigger] = lambda tgr: tgr,
) -> Shell:
    styled_children = tuple(child(look=looks.dropdown_item()) for child in children)
    return Shell(
        children=styled_children,
        trigger=trigger(disclosure),
        template="pudding/components/actions/dropdown.html",
    )


_FIRST = {"attrs": {"class": "rounded-r-none"}}
_LAST = {"attrs": {"class": "rounded-l-none border-l-0"}}
_MIDDLE = {"attrs": {"class": "rounded-none border-l-0"}}


def _morph_button(
    node: CoreTrigger | HasTrigger, **changes
) -> CoreTrigger | HasTrigger:
    """Apply style changes to a ButtonGroup member, adding a margin for non-outline variants."""

    def apply(trigger: CoreTrigger) -> dict:
        # if trigger.look != "outline":
        #     changes["attrs"] = merge_attrs(changes.get("attrs", {}), {"class": "mr-px"})
        return changes

    match node:
        case CoreTrigger():
            return node(**apply(node))
        case HasTrigger():
            return node(trigger=node.trigger(**apply(node.trigger)))
        case _:
            raise TypeError(
                f"ButtonGroup expects a Trigger or HasTrigger, got {type(node).__name__}"
            )


def ButtonGroup(
    children: Sequence[CoreTrigger | HasTrigger], extra_css: str = ""
) -> Group:
    """Group buttons into a joined visual strip."""
    css = f"flex {extra_css}"

    if len(children) <= 1:
        return Group(children=[children[0]], css=css)

    first, *middle, last = children
    return Group(
        css=css,
        children=(
            _morph_button(first, **_FIRST),
            *(_morph_button(node, **_MIDDLE) for node in middle),
            _morph_button(last, **_LAST),
        ),
    )
