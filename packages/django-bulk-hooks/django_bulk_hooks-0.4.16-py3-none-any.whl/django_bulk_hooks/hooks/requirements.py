from dataclasses import dataclass, field
from typing import FrozenSet, Optional


@dataclass(frozen=True)
class HookRequirements:
    """
    Declarative requirements for a hook handler.
    """

    old_records: bool = False
    new_records: bool = True
    preload_related: FrozenSet[str] = field(default_factory=frozenset)
    prefetch_related: FrozenSet[str] = field(default_factory=frozenset)
    batch_aware: bool = False
    max_batch_size: Optional[int] = None

    @classmethod
    def none(cls) -> "HookRequirements":
        return cls(old_records=False, new_records=False)

    @classmethod
    def standard(cls) -> "HookRequirements":
        return cls(old_records=False, new_records=True)

    @classmethod
    def full(cls) -> "HookRequirements":
        return cls(old_records=True, new_records=True)
