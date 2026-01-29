"""
Agent system for PinkyClawd.

Provides different agent personalities and capabilities for various
coding tasks like building, planning, and exploration.
"""

from pinkyclawd.agent.base import Agent, AgentMode, AgentPermissions
from pinkyclawd.agent.build import BuildAgent, get_build_agent
from pinkyclawd.agent.plan import PlanAgent, get_plan_agent
from pinkyclawd.agent.explore import ExploreAgent, get_explore_agent
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
    "BuildAgent",
    "get_build_agent",
    "PlanAgent",
    "get_plan_agent",
    "ExploreAgent",
    "get_explore_agent",
    "AgentRegistry",
    "get_agent_registry",
    "get_agent",
    "list_agents",
    "cycle_agent",
]
