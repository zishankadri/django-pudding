"""
HTML "frame" abstraction for HTMX/Alpine-driven partial updates.

A `Frame` represents an addressable region of a page (identified by
`target_id`) that can be rendered server-side and later replaced via an
HTMX response carrying the appropriate `HX-*` headers.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import SafeString

from pudding.exceptions import TriggerNormalizationError

DEFAULT_FRAME_TEMPLATE_STRING = """<div id="{{ target_id }}">
    {{ default_content }}
</div>"""


@dataclass(frozen=True)
class FilledFrame:
    """A frame populated with content, ready to be compiled into an HTTP response."""

    target_id: str
    content: str
    reswap: str
    event_triggers: dict[str, Any] | str

    def render_as_oob(self) -> SafeString | str:
        """Wrap content in an HTMX out-of-band swap container."""
        return format_html(
            '<div id="{target_id}" hx-swap-oob="{reswap}">{content}</div>',
            target_id=self.target_id,
            reswap=self.reswap,
            content=self.content,
        )


@dataclass(frozen=True)
class Frame:
    """
    An area on an HTML page.
    Content can be sent to it with a response that has the correct headers.
    """

    target_id: str
    template: str | None = None
    default_content: str | None = None
    reswap: str = "innerHTML"
    event_trigger: (
        Callable[[str], dict[str, Any] | str] | dict[str, Any] | str | None
    ) = None
    loading_attrs: Callable[[str], dict[str, str]] | None = None

    def render(self, request: HttpRequest) -> SafeString:
        """
        Render the frame's initial shell/container for a full page load.
        Frame content can be populated later via `fill()`.
        """

        ctx = {"target_id": self.target_id, "default_content": self.default_content}

        if self.template is None:
            return Template(DEFAULT_FRAME_TEMPLATE_STRING).render(Context(ctx))

        return render_to_string(self.template, context=ctx, request=request)

    def fill(self, content: str, target_id: str | None = None) -> FilledFrame:
        """Populate the frame with content, returning a `FilledFrame`"""

        target_id = target_id if target_id is not None else self.target_id
        raw_trigger = (
            self.event_trigger(target_id)
            if callable(self.event_trigger)
            else self.event_trigger
        )

        return FilledFrame(
            target_id=target_id,
            content=conditional_escape(content),
            reswap=self.reswap,
            event_triggers=raw_trigger if raw_trigger else {},
        )

    @property
    def loading_mod(self) -> dict[str, dict[str, str]]:
        """
        Return default modifiers for a `Trigger` to open this frame
        and display a loading spinner upon being clicked.

        Usage:
            my_trigger(**frame.loading_mods)
        """

        return self.loading_mod_for(self.target_id)

    def loading_mod_for(
        self, target_id: str | None = None
    ) -> dict[str, dict[str, str]]:
        """
        Return modifiers for a `Trigger` targeting a specific frame context.

        Allows overriding the default target ID dynamically.

        Usage:
            my_trigger(**frame.loading_mods_for("custom-target-id"))
        """
        target_id = target_id if target_id is not None else self.target_id
        loading_attrs = self.loading_attrs(target_id) if self.loading_attrs else {}

        return {"attrs": loading_attrs}

    def __call__(self, **kwargs: Any) -> Any:
        return replace(self, **kwargs)


def normalize_event(value: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        triggers = {}
        for raw_event in value.split(","):
            event = raw_event.strip()
            if not event:
                # Skip empty tokens from stray/trailing/double commas,
                # e.g. "event1,,event2" or "event1, ".
                continue
            triggers[event] = True
        return triggers

    elif isinstance(value, dict):
        return value
    else:
        raise TriggerNormalizationError(
            f"Unsupported value type {type(value).__name__!r}; expected str or dict."
        )


def FrameResponse(
    *frames: FilledFrame,
    trigger_events: list[dict[str, Any]] | None = None,
    push_action_url: dict | None = None,
) -> HttpResponse:
    """
    Compiles one or more FilledFrames into a single Django HttpResponse.

    The first frame acts as the primary payload. Subsequent frames are
    rendered as HTMX out-of-band (OOB) swaps.
    """
    if not frames:
        raise ValueError("At least one frame must be provided to ship().")

    primary_frame = frames[0]
    oob_frames = frames[1:]

    body_parts = [primary_frame.content] + [f.render_as_oob() for f in oob_frames]
    body = "\n".join(body_parts)

    response = HttpResponse(body)

    response["HX-Retarget"] = f"#{primary_frame.target_id}"
    response["HX-Reswap"] = primary_frame.reswap

    merged_triggers: dict[str, Any] = {}
    for frame in frames:
        merged_triggers |= normalize_event(frame.event_triggers)
    for trigger in trigger_events or []:
        merged_triggers |= normalize_event(trigger)
    if merged_triggers:
        response["HX-Trigger"] = json.dumps(merged_triggers)

    if push_action_url:
        response["HX-Push-Url"] = reverse(
            "pudding:run_action",
            kwargs={
                "domain_slug": push_action_url["domain_slug"],
                "action_slug": push_action_url["action_slug"],
            },
        )

    return response
