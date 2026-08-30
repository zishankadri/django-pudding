from __future__ import annotations

from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from pudding.domains import Domain

from pudding.exceptions import DomainNotRegistered, ImproperlyConfigured


class DomainRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, Domain] = {}

    @overload
    def register[T: Domain](self, domain_or_class: type[T]) -> type[T]: ...

    @overload
    def register[T: Domain](self, domain_or_class: T) -> T: ...

    def register(self, domain_or_class: type[Domain] | Domain) -> type[Domain] | Domain:
        if isinstance(domain_or_class, type):
            domain_name = domain_or_class.__name__
        else:
            domain_name = type(domain_or_class).__name__

        slug: str | None = getattr(domain_or_class, "slug", None)
        if slug is None:
            raise ValueError(f"'slug' must be defined on the Domain {domain_name}.")

        if slug in self._registry:
            existing_domain_name = self._registry[slug].__class__.__name__

            raise ImproperlyConfigured(
                f"The domain identifier '{slug}' for '{domain_name}' "
                f"clashes with the identifier for '{existing_domain_name}'.\n"
                f"\tHINT: Define or change the 'slug' attribute on the definition for "
                f"'{domain_name}' or '{existing_domain_name}'."
            )

        if isinstance(domain_or_class, type):
            self._registry[slug] = domain_or_class()
        else:
            self._registry[slug] = domain_or_class

        return domain_or_class

    def get(self, identifier: str) -> Domain:
        try:
            return self._registry[identifier]
        except KeyError:
            raise DomainNotRegistered(
                f"The domain identifier '{identifier}' is not registered. "
                f"Available identifiers: {list(self._registry.keys())}"
            )

    def get_all(self) -> dict[str, Domain]:
        return dict(self._registry)


_registry = DomainRegistry()

register = _registry.register
get = _registry.get
get_all = _registry.get_all
