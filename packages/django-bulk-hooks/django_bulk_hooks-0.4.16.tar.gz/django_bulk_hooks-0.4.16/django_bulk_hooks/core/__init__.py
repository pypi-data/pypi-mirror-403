"""
Core intent-centric architecture primitives.
"""

from .intent import IntentBuilder, OperationIntent
from .context import OperationContext
from .changeset import ChangeSet, RecordChange
from .conditions import (
    ChangesFrom,
    ChangesTo,
    HasChanged,
    HookCondition,
    IsEqual,
)

__all__ = [
    "IntentBuilder",
    "OperationIntent",
    "OperationContext",
    "ChangeSet",
    "RecordChange",
    "HookCondition",
    "HasChanged",
    "IsEqual",
    "ChangesTo",
    "ChangesFrom",
]
