"""
Core module for PinkyClawd.

Provides centralized state management, project instances, and dependency injection.

Usage:
    from pinkyclawd.core import get_state_factory, get_project_instance

    # Access components via state factory
    factory = get_state_factory()
    context_manager = factory.context_manager
    event_bus = factory.event_bus

    # Or use convenience functions
    from pinkyclawd.core import get_context_manager, get_event_bus
"""

from __future__ import annotations

# State Factory
from pinkyclawd.core.state import (
    StateFactory,
    LazyComponent,
    get_state_factory,
    reset_state_factory,
    # Convenience functions for backward compatibility
    get_context_manager,
    get_event_bus,
    get_session_manager,
    get_storage,
    get_rlm_handler,
    get_archiver,
    get_searcher,
    get_retriever,
    get_embedding_manager,
    get_graph_storage,
    get_graph_ingester,
    get_graph_traverser,
    get_graph_searcher,
    get_config,
    get_theme_manager,
)

# Project Instance
from pinkyclawd.core.instance import (
    ProjectContext,
    ProjectInstance,
    get_project_instance,
    get_project_context,
    initialize_project,
)

# Container (optional DI)
from pinkyclawd.core.container import (
    Container,
    ScopedContainer,
    Registration,
    get_container,
    reset_container,
)

__all__ = [
    # State Factory
    "StateFactory",
    "LazyComponent",
    "get_state_factory",
    "reset_state_factory",
    # Convenience functions
    "get_context_manager",
    "get_event_bus",
    "get_session_manager",
    "get_storage",
    "get_rlm_handler",
    "get_archiver",
    "get_searcher",
    "get_retriever",
    "get_embedding_manager",
    "get_graph_storage",
    "get_graph_ingester",
    "get_graph_traverser",
    "get_graph_searcher",
    "get_config",
    "get_theme_manager",
    # Project Instance
    "ProjectContext",
    "ProjectInstance",
    "get_project_instance",
    "get_project_context",
    "initialize_project",
    # Container
    "Container",
    "ScopedContainer",
    "Registration",
    "get_container",
    "reset_container",
]
