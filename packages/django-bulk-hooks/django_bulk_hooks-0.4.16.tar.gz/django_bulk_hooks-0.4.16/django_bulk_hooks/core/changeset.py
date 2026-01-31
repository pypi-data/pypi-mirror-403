from __future__ import annotations

import logging
from typing import Any, FrozenSet, Iterable, Optional, Tuple

from django.db.models import Model

from .context import OperationContext

logger = logging.getLogger(__name__)


class RecordChange:
    """
    Single record change with context awareness.
    """

    __slots__ = ("_new", "_old", "_context", "_changed_fields_cache")

    def __init__(
        self,
        new_record: Model,
        old_record: Optional[Model],
        context: Optional[OperationContext] = None,
    ):
        self._new = new_record
        self._old = old_record
        self._context = context
        self._changed_fields_cache: Optional[FrozenSet[str]] = None

    @property
    def new_record(self) -> Model:
        return self._new

    @property
    def old_record(self) -> Optional[Model]:
        return self._old

    @property
    def pk(self) -> Any:
        return self._new.pk if self._new else None

    @property
    def context(self) -> Optional[OperationContext]:
        return self._context

    def has_changed(self, field_name: str) -> bool:
        if self._context is not None and not self._context.is_field_in_scope(field_name):
            return False
        if self._old is None:
            return False
        return field_name in self.changed_fields

    @property
    def changed_fields(self) -> FrozenSet[str]:
        if self._changed_fields_cache is not None:
            return self._changed_fields_cache
        if self._old is None:
            self._changed_fields_cache = frozenset()
            return self._changed_fields_cache

        from django_bulk_hooks.operations.field_utils import get_changed_fields

        all_changed = get_changed_fields(self._old, self._new, self._new.__class__)
        if self._context is not None and self._context.intent.update_fields is not None:
            scoped = all_changed & self._context.intent.update_fields
            logger.debug(
                "[RECORD_CHANGE] pk=%s: all_changed=%s, update_fields=%s, scoped=%s",
                self.pk,
                all_changed,
                self._context.intent.update_fields,
                scoped,
            )
            self._changed_fields_cache = frozenset(scoped)
        else:
            logger.debug(
                "[RECORD_CHANGE] pk=%s: all_changed=%s (no field scope filtering)",
                self.pk,
                all_changed,
            )
            self._changed_fields_cache = frozenset(all_changed)
        return self._changed_fields_cache

    def get_old_value(self, field_name: str) -> Any:
        if self._old is None:
            return None
        return getattr(self._old, field_name, None)

    def get_new_value(self, field_name: str) -> Any:
        return getattr(self._new, field_name, None)


class ChangeSet:
    """
    Immutable view over operation changes.
    """

    __slots__ = ("_context", "_changes", "_pk_index")

    def __init__(self, context: OperationContext, changes: Tuple[RecordChange, ...]):
        self._context = context
        self._changes = changes
        self._pk_index = {c.pk: c for c in changes if c.pk is not None}

    @classmethod
    def from_context(cls, context: OperationContext) -> "ChangeSet":
        logger.debug(
            "[CHANGESET] Building ChangeSet for model=%s, operation=%s",
            context.model_cls.__name__,
            context.operation_type,
        )
        new_records = context.new_records
        old_records_map = context.old_records_map
        
        logger.info(
            "[CHANGESET] Creating changes: new_records=%d, old_records=%d",
            len(new_records),
            len(old_records_map),
        )
        
        changes = tuple(
            RecordChange(
                new_record=new,
                old_record=old_records_map.get(new.pk),
                context=context,
            )
            for new in new_records
        )
        
        logger.debug("[CHANGESET] ChangeSet created with %d changes", len(changes))
        return cls(context, changes)

    @property
    def context(self) -> OperationContext:
        return self._context

    @property
    def intent(self):
        return self._context.intent

    @property
    def operation_type(self) -> str:
        return self._context.operation_type

    @property
    def model_cls(self) -> type:
        return self._context.model_cls

    @property
    def new_records(self) -> list[Model]:
        return [c.new_record for c in self._changes]

    @property
    def old_records(self) -> list[Model]:
        return [c.old_record for c in self._changes if c.old_record is not None]

    @property
    def changes(self) -> Tuple[RecordChange, ...]:
        return self._changes

    def get_change(self, pk: Any) -> Optional[RecordChange]:
        return self._pk_index.get(pk)

    def has_field_changed(self, pk: Any, field_name: str) -> bool:
        change = self._pk_index.get(pk)
        return change.has_changed(field_name) if change else False

    def __len__(self) -> int:
        return len(self._changes)

    def __iter__(self):
        return iter(self._changes)

    def chunk(self, chunk_size: int) -> Iterable["ChangeSet"]:
        for i in range(0, len(self._changes), chunk_size):
            chunk_changes = self._changes[i : i + chunk_size]
            yield ChangeSet(self._context, chunk_changes)
