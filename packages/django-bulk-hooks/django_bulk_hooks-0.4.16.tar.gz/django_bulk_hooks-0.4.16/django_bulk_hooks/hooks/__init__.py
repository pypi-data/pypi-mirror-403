"""
Declarative hook system for intent-centric architecture.
"""

from .requirements import HookRequirements
from .base import Hook
from .decorators import hook

__all__ = [
    "HookRequirements",
    "Hook",
    "hook",
]
