"""
Dependency Injection container for PinkyClawd.

Provides a lightweight DI container for advanced use cases where
the StateFactory pattern isn't sufficient (e.g., testing with mocks).

Usage:
    from pinkyclawd.core import Container

    # Register a mock
    container = Container()
    container.register("storage", MockStorage())

    # Resolve dependency
    storage = container.resolve("storage")
"""

from __future__ import annotations

import logging
from typing import TypeVar, Generic, Callable, Any, Protocol, overload
from threading import Lock

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Resolvable(Protocol):
    """Protocol for resolvable dependencies."""
    pass


class Container:
    """
    Lightweight dependency injection container.

    Supports:
    - Registration by name or type
    - Factory functions
    - Singleton and transient lifetimes
    - Scoped instances
    """

    def __init__(self) -> None:
        self._registrations: dict[str, Registration] = {}
        self._singletons: dict[str, Any] = {}
        self._lock = Lock()

    def register(
        self,
        name: str,
        instance: T | None = None,
        factory: Callable[[], T] | None = None,
        singleton: bool = True,
    ) -> None:
        """
        Register a dependency.

        Args:
            name: Name to register under
            instance: Pre-created instance (if singleton)
            factory: Factory function to create instances
            singleton: Whether to cache the instance
        """
        with self._lock:
            if instance is not None:
                self._registrations[name] = Registration(
                    factory=lambda: instance,
                    singleton=True,
                )
                self._singletons[name] = instance
            elif factory is not None:
                self._registrations[name] = Registration(
                    factory=factory,
                    singleton=singleton,
                )
            else:
                raise ValueError("Must provide either instance or factory")

        logger.debug(f"Registered: {name} (singleton={singleton})")

    def register_factory(
        self,
        name: str,
        factory: Callable[[], T],
        singleton: bool = True,
    ) -> None:
        """Register a factory function."""
        self.register(name, factory=factory, singleton=singleton)

    def resolve(self, name: str) -> Any:
        """
        Resolve a dependency by name.

        Args:
            name: Registered name

        Returns:
            The resolved instance

        Raises:
            KeyError: If name is not registered
        """
        if name not in self._registrations:
            raise KeyError(f"Dependency not registered: {name}")

        registration = self._registrations[name]

        if registration.singleton:
            if name not in self._singletons:
                with self._lock:
                    if name not in self._singletons:
                        self._singletons[name] = registration.factory()
            return self._singletons[name]

        return registration.factory()

    def try_resolve(self, name: str) -> Any | None:
        """
        Try to resolve a dependency, returning None if not found.

        Args:
            name: Registered name

        Returns:
            The resolved instance or None
        """
        try:
            return self.resolve(name)
        except KeyError:
            return None

    def has(self, name: str) -> bool:
        """Check if a dependency is registered."""
        return name in self._registrations

    def unregister(self, name: str) -> None:
        """Remove a registration."""
        with self._lock:
            self._registrations.pop(name, None)
            self._singletons.pop(name, None)

    def clear(self) -> None:
        """Clear all registrations."""
        with self._lock:
            self._registrations.clear()
            self._singletons.clear()

    def reset_singletons(self) -> None:
        """Reset all singleton instances (for testing)."""
        with self._lock:
            self._singletons.clear()


class Registration:
    """Registration details for a dependency."""

    def __init__(self, factory: Callable[[], Any], singleton: bool = True):
        self.factory = factory
        self.singleton = singleton


class ScopedContainer:
    """
    Scoped container that inherits from a parent.

    Useful for request-scoped or test-scoped dependencies.
    """

    def __init__(self, parent: Container) -> None:
        self._parent = parent
        self._overrides: dict[str, Any] = {}

    def override(self, name: str, instance: Any) -> None:
        """Override a dependency for this scope."""
        self._overrides[name] = instance

    def resolve(self, name: str) -> Any:
        """Resolve from overrides first, then parent."""
        if name in self._overrides:
            return self._overrides[name]
        return self._parent.resolve(name)

    def clear(self) -> None:
        """Clear scope overrides."""
        self._overrides.clear()


# Global container
_container: Container | None = None
_container_lock = Lock()


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = Container()
    return _container


def reset_container() -> None:
    """Reset the global container (for testing)."""
    global _container
    with _container_lock:
        if _container is not None:
            _container.clear()
        _container = None
