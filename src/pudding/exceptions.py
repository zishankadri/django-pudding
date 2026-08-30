class ImproperlyConfigured(Exception):
    """Pudding is somehow improperly configured."""


class DomainNotRegistered(Exception):
    """Raised when trying to look up a domain that hasn't been registered."""


class TriggerNormalizationError(TypeError):
    """Raised when a trigger header or value cannot be normalized."""


class ActionNotRegistered(Exception):
    """Raised when trying to look up an action that hasn't been registered."""


class PermissionDenied(Exception):
    """The user did not have permission to do that."""
