"""
State Factory pattern for PinkyClawd.

Replaces singleton boilerplate with a centralized factory that manages
component lifecycle, enabling lazy initialization and proper cleanup.

Usage:
    from pinkyclawd.core import get_state_factory

    # Get a component (lazy-initialized)
    context_manager = get_state_factory().context_manager

    # Reset all state (for testing)
    get_state_factory().reset_all()
"""

from __future__ import annotations

import logging
from typing import TypeVar, Generic, Callable, Any
from threading import Lock
from dataclasses import dataclass, field
from contextlib import contextmanager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LazyComponent(Generic[T]):
    """
    Lazy-initialized component with thread-safe access.

    Delays initialization until first access and caches the instance.
    Supports reset for testing and cleanup for shutdown.
    """

    def __init__(
        self,
        factory: Callable[[], T],
        cleanup: Callable[[T], None] | None = None,
        name: str = "",
    ) -> None:
        """
        Initialize the lazy component.

        Args:
            factory: Callable that creates the component instance
            cleanup: Optional cleanup function called on reset
            name: Component name for logging
        """
        self._factory = factory
        self._cleanup = cleanup
        self._name = name
        self._instance: T | None = None
        self._lock = Lock()

    @property
    def instance(self) -> T:
        """Get or create the component instance."""
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    logger.debug(f"Initializing component: {self._name}")
                    self._instance = self._factory()
        return self._instance

    def reset(self) -> None:
        """Reset the component, calling cleanup if defined."""
        with self._lock:
            if self._instance is not None:
                if self._cleanup:
                    try:
                        self._cleanup(self._instance)
                    except Exception as e:
                        logger.warning(f"Cleanup error for {self._name}: {e}")
                self._instance = None
                logger.debug(f"Reset component: {self._name}")

    @property
    def is_initialized(self) -> bool:
        """Check if the component has been initialized."""
        return self._instance is not None


@dataclass
class StateFactory:
    """
    Centralized factory for all stateful components.

    Manages lifecycle of singletons, enabling:
    - Lazy initialization
    - Thread-safe access
    - Proper cleanup on reset
    - Testability through reset_all()
    """

    _instance: StateFactory | None = field(default=None, repr=False, init=False)
    _lock: Lock = field(default_factory=Lock, repr=False, init=False)
    _components: dict[str, LazyComponent] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._register_components()

    def _register_components(self) -> None:
        """Register all component factories."""
        # Context Manager
        self._components["context_manager"] = LazyComponent(
            factory=self._create_context_manager,
            cleanup=lambda cm: cm.reset(None) if hasattr(cm, "reset") else None,
            name="ContextManager",
        )

        # Event Bus
        self._components["event_bus"] = LazyComponent(
            factory=self._create_event_bus,
            cleanup=lambda eb: eb.clear() if hasattr(eb, "clear") else None,
            name="EventBus",
        )

        # Session Manager
        self._components["session_manager"] = LazyComponent(
            factory=self._create_session_manager,
            name="SessionManager",
        )

        # Storage
        self._components["storage"] = LazyComponent(
            factory=self._create_storage,
            cleanup=lambda s: s.close() if hasattr(s, "close") else None,
            name="Storage",
        )

        # RLM Handler
        self._components["rlm_handler"] = LazyComponent(
            factory=self._create_rlm_handler,
            name="RLMHandler",
        )

        # Archiver
        self._components["archiver"] = LazyComponent(
            factory=self._create_archiver,
            name="ContextArchiver",
        )

        # Searcher
        self._components["searcher"] = LazyComponent(
            factory=self._create_searcher,
            name="ContextSearcher",
        )

        # Retriever
        self._components["retriever"] = LazyComponent(
            factory=self._create_retriever,
            name="ContextRetriever",
        )

        # Embedding Manager
        self._components["embedding_manager"] = LazyComponent(
            factory=self._create_embedding_manager,
            name="EmbeddingManager",
        )

        # Graph components
        self._components["graph_storage"] = LazyComponent(
            factory=self._create_graph_storage,
            cleanup=lambda gs: gs.close() if hasattr(gs, "close") else None,
            name="GraphStorageAdapter",
        )

        self._components["graph_ingester"] = LazyComponent(
            factory=self._create_graph_ingester,
            name="GraphIngester",
        )

        self._components["graph_traverser"] = LazyComponent(
            factory=self._create_graph_traverser,
            name="GraphTraverser",
        )

        self._components["graph_searcher"] = LazyComponent(
            factory=self._create_graph_searcher,
            name="GraphSearcher",
        )

        # Config
        self._components["config"] = LazyComponent(
            factory=self._create_config,
            name="Settings",
        )

        # Theme Manager
        self._components["theme_manager"] = LazyComponent(
            factory=self._create_theme_manager,
            name="ThemeManager",
        )

    # =========================================================================
    # Component Properties
    # =========================================================================

    @property
    def context_manager(self):
        """Get the ContextManager instance."""
        return self._components["context_manager"].instance

    @property
    def event_bus(self):
        """Get the EventBus instance."""
        return self._components["event_bus"].instance

    @property
    def session_manager(self):
        """Get the SessionManager instance."""
        return self._components["session_manager"].instance

    @property
    def storage(self):
        """Get the Storage instance."""
        return self._components["storage"].instance

    @property
    def rlm_handler(self):
        """Get the RLMHandler instance."""
        return self._components["rlm_handler"].instance

    @property
    def archiver(self):
        """Get the ContextArchiver instance."""
        return self._components["archiver"].instance

    @property
    def searcher(self):
        """Get the ContextSearcher instance."""
        return self._components["searcher"].instance

    @property
    def retriever(self):
        """Get the ContextRetriever instance."""
        return self._components["retriever"].instance

    @property
    def embedding_manager(self):
        """Get the EmbeddingManager instance."""
        return self._components["embedding_manager"].instance

    @property
    def graph_storage(self):
        """Get the GraphStorageAdapter instance."""
        return self._components["graph_storage"].instance

    @property
    def graph_ingester(self):
        """Get the GraphIngester instance."""
        return self._components["graph_ingester"].instance

    @property
    def graph_traverser(self):
        """Get the GraphTraverser instance."""
        return self._components["graph_traverser"].instance

    @property
    def graph_searcher(self):
        """Get the GraphSearcher instance."""
        return self._components["graph_searcher"].instance

    @property
    def config(self):
        """Get the Settings instance."""
        return self._components["config"].instance

    @property
    def theme_manager(self):
        """Get the ThemeManager instance."""
        return self._components["theme_manager"].instance

    # =========================================================================
    # Factory Methods (lazy imports to avoid circular dependencies)
    # =========================================================================

    def _create_context_manager(self):
        from pinkyclawd.rlm.context import ContextManager
        return ContextManager()

    def _create_event_bus(self):
        from pinkyclawd.events import EventBus
        return EventBus()

    def _create_session_manager(self):
        from pinkyclawd.session.manager import SessionManager
        return SessionManager()

    def _create_storage(self):
        # Get config without triggering circular dependency
        try:
            from pinkyclawd.config.settings import load_config
            config = load_config()
            storage_backend = config.storage_backend
        except Exception:
            storage_backend = "sqlite"  # Default to SQLite

        if storage_backend == "json":
            from pinkyclawd.config.storage import JSONStorageAdapter
            return JSONStorageAdapter()
        else:
            from pinkyclawd.config.storage import Storage
            return Storage()

    def _create_rlm_handler(self):
        from pinkyclawd.rlm.handler import RLMHandler
        return RLMHandler()

    def _create_archiver(self):
        from pinkyclawd.rlm.archive import ContextArchiver
        return ContextArchiver()

    def _create_searcher(self):
        from pinkyclawd.rlm.search import ContextSearcher
        return ContextSearcher()

    def _create_retriever(self):
        from pinkyclawd.rlm.retrieve import ContextRetriever
        return ContextRetriever()

    def _create_embedding_manager(self):
        from pinkyclawd.rlm.embedding import EmbeddingManager
        return EmbeddingManager()

    def _create_graph_storage(self):
        from pinkyclawd.rlm.graph import GraphStorageAdapter
        return GraphStorageAdapter()

    def _create_graph_ingester(self):
        from pinkyclawd.rlm.graph import GraphIngester
        return GraphIngester()

    def _create_graph_traverser(self):
        from pinkyclawd.rlm.graph import GraphTraverser
        return GraphTraverser()

    def _create_graph_searcher(self):
        from pinkyclawd.rlm.graph import GraphSearcher
        return GraphSearcher()

    def _create_config(self):
        from pinkyclawd.config.settings import load_config
        return load_config()

    def _create_theme_manager(self):
        from pinkyclawd.config.theme import ThemeManager
        return ThemeManager()

    # =========================================================================
    # Lifecycle Management
    # =========================================================================

    def reset(self, component_name: str) -> None:
        """Reset a specific component."""
        if component_name in self._components:
            self._components[component_name].reset()
        else:
            logger.warning(f"Unknown component: {component_name}")

    def reset_all(self) -> None:
        """Reset all components (for testing)."""
        logger.info("Resetting all components")
        for name, component in self._components.items():
            component.reset()

    def is_initialized(self, component_name: str) -> bool:
        """Check if a specific component is initialized."""
        if component_name in self._components:
            return self._components[component_name].is_initialized
        return False

    @contextmanager
    def scoped(self):
        """
        Context manager for scoped state.

        Useful for testing - automatically resets all state on exit.

        Usage:
            with get_state_factory().scoped():
                # Test code here
                ...
            # All state is reset after exiting
        """
        try:
            yield self
        finally:
            self.reset_all()


# Global factory instance
_state_factory: StateFactory | None = None
_factory_lock = Lock()


def get_state_factory() -> StateFactory:
    """Get the global state factory instance."""
    global _state_factory
    if _state_factory is None:
        with _factory_lock:
            if _state_factory is None:
                _state_factory = StateFactory()
    return _state_factory


def reset_state_factory() -> None:
    """Reset the global state factory (for testing)."""
    global _state_factory
    with _factory_lock:
        if _state_factory is not None:
            _state_factory.reset_all()
            _state_factory = None


# =========================================================================
# Convenience Functions (backward compatibility)
# =========================================================================

def get_context_manager():
    """Get the ContextManager instance."""
    return get_state_factory().context_manager


def get_event_bus():
    """Get the EventBus instance."""
    return get_state_factory().event_bus


def get_session_manager():
    """Get the SessionManager instance."""
    return get_state_factory().session_manager


def get_storage():
    """Get the Storage instance."""
    return get_state_factory().storage


def get_rlm_handler():
    """Get the RLMHandler instance."""
    return get_state_factory().rlm_handler


def get_archiver():
    """Get the ContextArchiver instance."""
    return get_state_factory().archiver


def get_searcher():
    """Get the ContextSearcher instance."""
    return get_state_factory().searcher


def get_retriever():
    """Get the ContextRetriever instance."""
    return get_state_factory().retriever


def get_embedding_manager():
    """Get the EmbeddingManager instance."""
    return get_state_factory().embedding_manager


def get_graph_storage():
    """Get the GraphStorageAdapter instance."""
    return get_state_factory().graph_storage


def get_graph_ingester():
    """Get the GraphIngester instance."""
    return get_state_factory().graph_ingester


def get_graph_traverser():
    """Get the GraphTraverser instance."""
    return get_state_factory().graph_traverser


def get_graph_searcher():
    """Get the GraphSearcher instance."""
    return get_state_factory().graph_searcher


def get_config():
    """Get the Settings instance."""
    return get_state_factory().config


def get_theme_manager():
    """Get the ThemeManager instance."""
    return get_state_factory().theme_manager
