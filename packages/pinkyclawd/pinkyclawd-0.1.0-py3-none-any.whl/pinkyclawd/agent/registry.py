"""
Agent registry for managing available agents.

Provides agent lookup, registration, and cycling functionality.
"""

from __future__ import annotations

import logging
from typing import Any

from pinkyclawd.agent.base import Agent, AgentMode
from pinkyclawd.agent.build import get_build_agent
from pinkyclawd.agent.plan import get_plan_agent
from pinkyclawd.agent.explore import get_explore_agent
from pinkyclawd.config.settings import get_config, AgentConfig

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry of available agents.

    Manages built-in agents and custom agents from configuration.
    """

    _instance: AgentRegistry | None = None

    def __new__(cls) -> AgentRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._agents: dict[str, Agent] = {}
        self._current_agent_id: str = "build"
        self._agent_order: list[str] = []

        # Register built-in agents
        self._register_builtin_agents()

        # Load custom agents from config
        self._load_custom_agents()

        self._initialized = True

    def _register_builtin_agents(self) -> None:
        """Register the built-in agents."""
        self.register(get_build_agent())
        self.register(get_plan_agent())
        self.register(get_explore_agent())

    def _load_custom_agents(self) -> None:
        """Load custom agents from configuration."""
        config = get_config()

        for agent_id, agent_config in config.agent.items():
            if agent_id in self._agents:
                # Merge with existing agent
                existing = self._agents[agent_id]
                self._merge_agent_config(existing, agent_config)
            else:
                # Create new custom agent
                agent = self._create_from_config(agent_id, agent_config)
                self.register(agent)

    def _create_from_config(self, agent_id: str, config: AgentConfig) -> Agent:
        """Create an agent from configuration."""
        from pinkyclawd.agent.base import AgentPermissions

        permissions = AgentPermissions.from_dict(config.permission)

        return Agent(
            id=agent_id,
            name=agent_id.title(),
            description=config.description,
            system_prompt=config.prompt,
            mode=AgentMode(config.mode),
            permissions=permissions,
            model=config.model,
            temperature=config.temperature,
            top_p=config.top_p,
            max_steps=config.steps,
            color=config.color or "blue",
            hidden=config.hidden,
        )

    def _merge_agent_config(self, agent: Agent, config: AgentConfig) -> None:
        """Merge configuration into an existing agent."""
        if config.prompt:
            agent.system_prompt = config.prompt
        if config.model:
            agent.model = config.model
        if config.description:
            agent.description = config.description
        if config.color:
            agent.color = config.color
        if config.temperature is not None:
            agent.temperature = config.temperature
        if config.top_p is not None:
            agent.top_p = config.top_p
        if config.steps:
            agent.max_steps = config.steps
        if config.permission:
            from pinkyclawd.agent.base import AgentPermissions

            agent.permissions = AgentPermissions.from_dict(config.permission)

    def register(self, agent: Agent) -> None:
        """Register an agent."""
        self._agents[agent.id] = agent

        # Add to order if primary agent
        if agent.mode in (AgentMode.PRIMARY, AgentMode.ALL):
            if agent.id not in self._agent_order and not agent.hidden:
                self._agent_order.append(agent.id)

        logger.debug(f"Registered agent: {agent.id}")

    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            if agent_id in self._agent_order:
                self._agent_order.remove(agent_id)
            return True
        return False

    def get(self, agent_id: str) -> Agent | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def get_current(self) -> Agent:
        """Get the currently selected agent."""
        agent = self._agents.get(self._current_agent_id)
        if agent is None:
            # Fall back to build agent
            return get_build_agent()
        return agent

    def set_current(self, agent_id: str) -> bool:
        """Set the current agent."""
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        if agent.mode == AgentMode.SUBAGENT:
            logger.warning(f"Agent {agent_id} is subagent-only")
            return False

        self._current_agent_id = agent_id
        logger.info(f"Switched to agent: {agent_id}")
        return True

    def cycle(self, direction: int = 1) -> Agent:
        """
        Cycle to the next/previous agent.

        Args:
            direction: 1 for next, -1 for previous

        Returns:
            The newly selected agent
        """
        if not self._agent_order:
            return self.get_current()

        try:
            current_index = self._agent_order.index(self._current_agent_id)
        except ValueError:
            current_index = 0

        new_index = (current_index + direction) % len(self._agent_order)
        new_agent_id = self._agent_order[new_index]

        self.set_current(new_agent_id)
        return self.get_current()

    def list_primary(self) -> list[Agent]:
        """List agents that can be used as primary agents."""
        return [
            agent
            for agent in self._agents.values()
            if agent.mode in (AgentMode.PRIMARY, AgentMode.ALL) and not agent.hidden
        ]

    def list_subagents(self) -> list[Agent]:
        """List agents that can be used as subagents."""
        return [
            agent
            for agent in self._agents.values()
            if agent.mode in (AgentMode.SUBAGENT, AgentMode.ALL)
        ]

    def list_all(self) -> list[Agent]:
        """List all registered agents."""
        return list(self._agents.values())

    def to_dict(self) -> dict[str, Any]:
        """Export registry state."""
        return {
            "current": self._current_agent_id,
            "agents": {agent_id: agent.to_dict() for agent_id, agent in self._agents.items()},
            "order": self._agent_order,
        }

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry."""
    return AgentRegistry()


# Convenience functions


def get_agent(agent_id: str) -> Agent | None:
    """Get an agent by ID."""
    return get_agent_registry().get(agent_id)


def list_agents() -> list[Agent]:
    """List all primary agents."""
    return get_agent_registry().list_primary()


def cycle_agent(direction: int = 1) -> Agent:
    """Cycle to the next agent."""
    return get_agent_registry().cycle(direction)


def get_current_agent() -> Agent:
    """Get the current agent."""
    return get_agent_registry().get_current()


def set_current_agent(agent_id: str) -> bool:
    """Set the current agent."""
    return get_agent_registry().set_current(agent_id)
