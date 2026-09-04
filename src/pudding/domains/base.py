from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pudding import ui
    from pudding.actions.contracts import Action

from django.db import models

from pudding.actions.registry import ActionRegistry
from pudding.exceptions import ImproperlyConfigured


class Domain:
    """
    A high-level namespace to manage related resources and actions.

    Attributes:
        model: The primary Django model associated with this domain, if any.
        icon: UI icon identifier for this domain section.
        actions: Actions available within this domain.
        action_registry: Registry storing and managing the domain's actions.
    """

    def __init__(
        self,
        slug: str | None = None,
        icon: str | None = None,
        label: str | None = None,
        label_plural: str | None = None,
        actions: list[Action] | None = None,
        model: type[models.Model] | None = None,
    ) -> None:
        self.slug = slug or getattr(self, "slug", None)
        self.model = model or getattr(self, "model", None)
        self.icon = icon or getattr(self, "icon", None)
        self.actions = actions or getattr(self, "actions", [])

        self.action_registry = ActionRegistry()

        for action_instance in self.actions:
            self.action_registry.register(action_instance.slug, action_instance)

        if not self.slug or not isinstance(self.slug, str):
            raise ImproperlyConfigured(
                f"Domain '{self.__class__.__name__}' must define a string 'slug' attribute."
            )

        if model is not None:
            if label is None:
                label = str(model._meta.verbose_name).title()
            if label_plural is None:
                label_plural = str(model._meta.verbose_name_plural).title()

        self.label = (
            label
            or getattr(self, "label", None)
            or self.slug.replace("_", " ").replace("-", " ").title()
        )
        self.label_plural = (
            label_plural or getattr(self, "label_plural", None) or f"{self.label}s"
        )

    def get_action(self, action_slug: str) -> Action:
        return self.action_registry.get_action(action_slug)

    def has_permission(self, request, action):
        return True

    # --- Factory ----------------------------------------
    @classmethod
    def from_model(
        cls,
        model: type[models.Model],
        slug: str | None = None,
        icon: str | None = None,
        columns: Sequence[ui.Column | str] | None = None,
        **kwargs,
    ) -> Domain:
        from pudding import ui
        from pudding.actions import Add, Delete, Edit, View

        resolved_slug = slug or model._meta.model_name

        view = ui.Table(
            model=model,
            row_actions=[
                Edit().trigger(size="icon-sm"),
                Delete().trigger(size="icon-sm"),
            ],
            bulk_actions=[Delete().trigger],
            columns=columns or [],
        )

        actions: list[Action] = [
            View(view=view, header_actions=[Add().trigger]),
            Add(),
            Edit(),
            Delete(),
        ]

        return cls(
            slug=resolved_slug, icon=icon, model=model, actions=actions, **kwargs
        )
