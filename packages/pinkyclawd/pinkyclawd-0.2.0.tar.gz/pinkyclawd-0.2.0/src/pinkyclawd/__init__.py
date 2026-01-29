"""
PinkyClawd - AI-powered development tool with TUI interface.

A production-grade terminal user interface for AI-assisted coding,
featuring recursive language model context management, multi-provider
support, and a comprehensive tool system.
"""

__version__ = "0.1.0"
__author__ = "Michael Thornton"

from pinkyclawd.config.settings import Config, load_config
from pinkyclawd.events import EventBus, Event

__all__ = [
    "__version__",
    "Config",
    "load_config",
    "EventBus",
    "Event",
]
