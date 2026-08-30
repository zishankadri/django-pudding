import re

from pudding.actions.contracts import Action
from pudding.exceptions import ActionNotRegistered, ImproperlyConfigured

SLUG_REGEX = re.compile(r"^[\w-]+$")


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, Action] = {}

    def register(self, slug: str, action_item: Action | type[Action]) -> None:
        if not isinstance(slug, str):
            raise ImproperlyConfigured(
                f"Action slug must be a string, got {type(slug).__name__}."
            )

        if not SLUG_REGEX.match(slug):
            raise ImproperlyConfigured(
                f"Invalid Action slug: '{slug}'. "
                "Only letters, numbers, underscores (_), and hyphens (-) are allowed. "
                "No spaces, slashes or special characters."
            )

        if slug in self._actions:
            existing_action = self._actions[slug].__class__.__name__
            raise ImproperlyConfigured(
                f"Action slug '{slug}' is already registered by '{existing_action}'."
            )

        if isinstance(action_item, type):
            try:
                final_instance = action_item()
            except Exception as e:
                raise ImproperlyConfigured(
                    f"Failed to instantiate action class '{action_item.__name__}': {e}"
                ) from e
        else:
            final_instance = action_item

        if not isinstance(final_instance, Action):
            item_name = type(final_instance).__name__
            raise ImproperlyConfigured(
                f"Registered item '{item_name}' does not implement the Action protocol structure."
            )

        self._actions[slug] = final_instance

    def get_action(self, slug: str) -> Action:
        try:
            return self._actions[slug]
        except KeyError:
            raise ActionNotRegistered(
                f"The action slug '{slug}' is not registered. "
                f"Available actions: {list(self._actions.keys())}"
            )
