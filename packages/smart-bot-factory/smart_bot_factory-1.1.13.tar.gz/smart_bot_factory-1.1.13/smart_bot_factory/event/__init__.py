"""
Event модули smart_bot_factory
"""

from .decorators.registry import event_handler, global_handler, schedule_task
from .router import EventRouter
from .router_manager import RouterManager

__all__ = [
    "event_handler",
    "schedule_task",
    "global_handler",
    "EventRouter",
    "RouterManager",
]
