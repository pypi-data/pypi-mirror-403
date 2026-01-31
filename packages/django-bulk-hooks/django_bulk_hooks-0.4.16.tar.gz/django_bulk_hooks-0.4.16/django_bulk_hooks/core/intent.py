from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, FrozenSet, Iterable, Mapping, Optional
from typing import Literal
import uuid


@dataclass(frozen=True)
class OperationIntent:
    """
    Immutable description of what the user wants to do.

    This is the single source of truth for the entire operation.
    """

    # Identity
    operation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # What
    operation_type: Literal["create", "update", "delete"] = "update"
    model_cls: type | None = None

    # Target selection
    target_pks: Optional[tuple[Any, ...]] = None

    # Field updates (for update operations)
    field_values: Optional[Mapping[str, Any]] = None
    update_fields: Optional[FrozenSet[str]] = None
    unique_fields: Optional[FrozenSet[str]] = None

    # Execution options
    batch_size: Optional[int] = None
    ignore_conflicts: bool = False
    update_conflicts: bool = False
    bypass_hooks: bool = False

    # Database
    using_db: Optional[str] = None

    def is_field_in_scope(self, field_name: str) -> bool:
        """
        Check if a field is part of this operation's scope.

        If update_fields is None, all fields are in scope.
        """
        if self.update_fields is None:
            return True
        return field_name in self.update_fields

    def get_scoped_fields(self) -> FrozenSet[str]:
        """Return all fields in scope, resolving None to all model fields."""
        if self.update_fields is not None:
            return self.update_fields
        if self.model_cls is None:
            return frozenset()
        return frozenset(f.name for f in self.model_cls._meta.get_fields() if f.concrete and not f.many_to_many)


class IntentBuilder:
    """
    Fluent builder for OperationIntent with minimal validation.
    """

    def __init__(self, model_cls: type):
        self.model_cls = model_cls
        self._operation_type: Optional[str] = None
        self._target_pks: Optional[tuple[Any, ...]] = None
        self._field_values: Optional[Mapping[str, Any]] = None
        self._update_fields: Optional[FrozenSet[str]] = None
        self._unique_fields: Optional[FrozenSet[str]] = None
        self._options: dict[str, Any] = {}

    def for_create(self) -> "IntentBuilder":
        self._operation_type = "create"
        return self

    def for_update(self) -> "IntentBuilder":
        self._operation_type = "update"
        return self

    def for_delete(self) -> "IntentBuilder":
        self._operation_type = "delete"
        return self

    def targeting(self, pks: Iterable[Any]) -> "IntentBuilder":
        self._target_pks = tuple(pks)
        return self

    def setting(self, **field_values: Any) -> "IntentBuilder":
        self._field_values = MappingProxyType(dict(field_values))
        self._update_fields = frozenset(field_values.keys())
        return self

    def with_update_fields(self, fields: Iterable[str]) -> "IntentBuilder":
        self._update_fields = frozenset(fields)
        return self

    def with_unique_fields(self, fields: Optional[Iterable[str]]) -> "IntentBuilder":
        if fields is None:
            self._unique_fields = None
            return self
        self._unique_fields = frozenset(fields)
        return self

    def with_options(self, **options: Any) -> "IntentBuilder":
        self._options.update(options)
        return self

    def build(self) -> OperationIntent:
        if self._operation_type is None:
            raise ValueError("Operation type must be specified")
        if self.model_cls is None:
            raise ValueError("Model class must be provided")

        return OperationIntent(
            operation_type=self._operation_type,
            model_cls=self.model_cls,
            target_pks=self._target_pks,
            field_values=self._field_values,
            update_fields=self._update_fields,
            unique_fields=self._unique_fields,
            **self._options,
        )
