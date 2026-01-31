from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional, Set, Tuple

from django.db.models import Model

from .intent import OperationIntent

logger = logging.getLogger(__name__)


class OperationContext:
    """
    Lazy-loading wrapper around OperationIntent and database state.
    """

    __slots__ = (
        "intent",
        "_old_records_cache",
        "_new_records_cache",
        "_changeset_cache",
        "_select_related",
        "_prefetch_related",
    )

    def __init__(self, intent: OperationIntent):
        self.intent = intent
        self._old_records_cache: Optional[Mapping[Any, Model]] = None
        self._new_records_cache: Optional[Tuple[Model, ...]] = None
        self._changeset_cache = None
        self._select_related: Set[str] = set()
        self._prefetch_related: Set[str] = set()

    # Delegation to intent
    @property
    def operation_type(self) -> str:
        return self.intent.operation_type

    @property
    def model_cls(self) -> type:
        return self.intent.model_cls

    @property
    def operation_id(self):
        return self.intent.operation_id

    def is_field_in_scope(self, field_name: str) -> bool:
        return self.intent.is_field_in_scope(field_name)

    # Lazy data access
    @property
    def old_records_map(self) -> Mapping[Any, Model]:
        if self._old_records_cache is not None:
            logger.debug(
                "[CONTEXT] old_records_map: using cached data (%d records)",
                len(self._old_records_cache),
            )
            return self._old_records_cache

        if self.intent.operation_type == "create":
            logger.debug("[CONTEXT] old_records_map: CREATE operation, returning empty map")
            self._old_records_cache = MappingProxyType({})
            return self._old_records_cache

        if not self.intent.target_pks:
            logger.debug("[CONTEXT] old_records_map: no target_pks, returning empty map")
            self._old_records_cache = MappingProxyType({})
            return self._old_records_cache

        logger.info(
            "[CONTEXT] old_records_map: Loading from DB for model=%s, count=%d PKs",
            self.model_cls.__name__,
            len(self.intent.target_pks),
        )
        qs = self.model_cls._base_manager.filter(pk__in=self.intent.target_pks)
        if self.intent.using_db:
            qs = qs.using(self.intent.using_db)
        if self._select_related:
            qs = qs.select_related(*self._select_related)
        if self._prefetch_related:
            qs = qs.prefetch_related(*self._prefetch_related)

        records = qs.in_bulk(self.intent.target_pks)
        logger.info("[CONTEXT] old_records_map: Loaded %d records from DB", len(records))
        self._old_records_cache = MappingProxyType(records)
        return self._old_records_cache

    @property
    def new_records(self) -> Tuple[Model, ...]:
        if self._new_records_cache is not None:
            logger.debug(
                "[CONTEXT] new_records: using cached data (%d records)",
                len(self._new_records_cache),
            )
            return self._new_records_cache

        if self.intent.operation_type == "delete":
            logger.debug("[CONTEXT] new_records: DELETE operation, using old_records_map")
            self._new_records_cache = tuple(self.old_records_map.values())
            return self._new_records_cache

        if not self.intent.target_pks:
            logger.debug("[CONTEXT] new_records: no target_pks, returning empty tuple")
            self._new_records_cache = tuple()
            return self._new_records_cache

        logger.info(
            "[CONTEXT] new_records: Loading from DB for model=%s, count=%d PKs",
            self.model_cls.__name__,
            len(self.intent.target_pks),
        )
        qs = self.model_cls._base_manager.filter(pk__in=self.intent.target_pks)
        if self.intent.using_db:
            qs = qs.using(self.intent.using_db)
        if self._select_related:
            qs = qs.select_related(*self._select_related)
        if self._prefetch_related:
            qs = qs.prefetch_related(*self._prefetch_related)

        self._new_records_cache = tuple(qs)
        logger.info("[CONTEXT] new_records: Loaded %d records from DB", len(self._new_records_cache))
        return self._new_records_cache

    @property
    def changeset(self):
        if self._changeset_cache is not None:
            return self._changeset_cache

        from .changeset import ChangeSet

        self._changeset_cache = ChangeSet.from_context(self)
        return self._changeset_cache

    # Preloading
    def with_preloaded_relations(self, relations: Iterable[str]) -> "OperationContext":
        relations_set = set(relations)
        if relations_set != self._select_related:
            self._invalidate_caches()
        self._select_related = relations_set
        return self

    def with_prefetched_relations(self, relations: Iterable[str]) -> "OperationContext":
        relations_set = set(relations)
        if relations_set != self._prefetch_related:
            self._invalidate_caches()
        self._prefetch_related = relations_set
        return self

    # Instance injection
    def with_instances(
        self,
        new_records: Optional[Tuple[Model, ...]] = None,
        old_records_map: Optional[Mapping[Any, Model]] = None,
    ) -> "OperationContext":
        if new_records is not None:
            self._new_records_cache = new_records
        if old_records_map is not None:
            self._old_records_cache = MappingProxyType(dict(old_records_map))
        self._changeset_cache = None
        return self

    def clear_caches(self) -> None:
        self._invalidate_caches()

    def _invalidate_caches(self) -> None:
        self._old_records_cache = None
        # For create, new_records come only from with_instances(); do not clear
        # so before_create hooks receive the unsaved instances (fixes regression
        # when preload_related from after_create hooks triggers invalidation).
        if self.intent.operation_type != "create":
            self._new_records_cache = None
        self._changeset_cache = None
