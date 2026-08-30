"""
Built in components of HTMX/Alpine wiring for frames
"""

from pudding.ui.primitives import Frame

modal_frame = Frame(
    template="pudding/frames/modal_frame.html",
    target_id="pudding-modal",
    event_trigger=lambda target_id: f"open-{target_id}",
    loading_attrs=lambda target_id: {
        "@click": f"$dispatch('open-{target_id}')",
        "hx-indicator": f"#{target_id}-dialog",  # TODO: Remove this
        "hx-sync": f"#{target_id}:replace",
        "hx-target": f"#{target_id}",
        "hx-swap": "innerHTML",
    },
)

view_frame = Frame(
    target_id="view-frame",
    template="pudding/frames/view_frame.html",
    loading_attrs=lambda target_id: {
        "@click": f"$dispatch('show-loading-{target_id}')",
        "@htmx:response-error": f"$dispatch('show-error-{target_id}')",
        "@htmx:send-error": f"$dispatch('show-error-{target_id}')",
        "hx-target": f"#{target_id}",
        "hx-sync": f"#{target_id}:replace",
        "hx-swap": "innerHTML",
    },
)

breadcrumb_frame = Frame(target_id="breadcrumb-frame")
header_triggers_frame = Frame(target_id="header-triggers-frame")
