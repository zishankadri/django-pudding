import inspect

import pytest

from pudding.actions import Modal
from pudding.ui import ActionModal


def test_modal_hook_signature_matches_action_modal():
    modal_params = inspect.signature(ActionModal).parameters
    hook_params = inspect.signature(Modal).parameters

    expected_params = {
        name: param for name, param in modal_params.items() if name != "action"
    }

    for name in expected_params:
        assert name in hook_params, (
            f"Parameter '{name}' exists on ActionModal, but was not added to modal_hook!"
        )

    for name, param in expected_params.items():
        # Functions use parameter defaults while dataclasses use field(default_factory=...).
        # Because we can't pass field() to a function, the hook uses UNSET/None as sentinels.
        # Strip those sentinels here.
        modal_ann = (
            str(param.annotation).replace(" | UnsetType", "").replace(" | None", "")
        )
        hook_ann = (
            str(hook_params[name].annotation)
            .replace(" | UnsetType", "")
            .replace(" | None", "")
        )

        assert modal_ann == hook_ann, (
            f"Type mismatch for parameter '{name}': "
            f"ActionModal has {param.annotation}, hook has {hook_params[name].annotation}"
        )
