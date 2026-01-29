"""
Agent system for PinkyClawd.

Provides different agent personalities and capabilities for various
coding tasks like building, planning, and exploration.
"""

from pinkyclawd.agent.base import Agent, AgentMode, AgentPermissions
from pinkyclawd.agent.build import create_build_agent, get_build_agent
from pinkyclawd.agent.plan import create_plan_agent, get_plan_agent
from pinkyclawd.agent.explore import create_explore_agent, get_explore_agent
from pinkyclawd.agent.registry import (
    AgentRegistry,
    get_agent_registry,
    get_agent,
    list_agents,
    cycle_agent,
)

__all__ = [
    "Agent",
    "AgentMode",
    "AgentPermissions",
    "create_build_agent",
    "get_build_agent",
    "create_plan_agent",
    "get_plan_agent",
    "create_explore_agent",
    "get_explore_agent",
    "AgentRegistry",
    "get_agent_registry",
    "get_agent",
    "list_agents",
    "cycle_agent",
]
