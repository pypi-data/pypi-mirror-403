"""
HookQuerySet - Django QuerySet with hook support.

This is a thin coordinator that delegates all complex logic to services.
It follows the Facade pattern, providing a simple interface over the
complex coordination required for bulk operations with hooks.
"""

import logging

from django.conf import settings
from django.db import models
from django.db import transaction

from django_bulk_hooks.helpers import extract_pks

logger = logging.getLogger(__name__)


class HookQuerySet(models.QuerySet):
    """
    QuerySet with hook support.

    This is a thin facade over BulkOperationCoordinator. It provides
    backward-compatible API for Django's QuerySet while integrating
    the full hook lifecycle.

    Key design principles:
    - Minimal logic (< 10 lines per method)
    - No business logic (delegate to coordinator)
    - No conditionals (let services handle it)
    - Transaction boundaries only
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coordinator = None

    @classmethod
    def with_hooks(cls, queryset):
        """
        Apply hook functionality to any queryset.

        This enables hooks to work with any manager by applying hook
        capabilities at the queryset level rather than through inheritance.

        Args:
            queryset: Any Django QuerySet instance

        Returns:
            HookQuerySet instance with the same query parameters
        """
        if isinstance(queryset, cls):
            return queryset  # Already has hooks

        # Create a new HookQuerySet with the same parameters as the original queryset
        hook_qs = cls(
            model=queryset.model,
            query=queryset.query,
            using=queryset._db,
            hints=getattr(queryset, "_hints", {}),
        )

        # Preserve any additional attributes from the original queryset
        # This allows composition with other queryset enhancements
        cls._preserve_queryset_attributes(hook_qs, queryset)

        return hook_qs

    @classmethod
    def _preserve_queryset_attributes(cls, hook_qs, original_qs):
        """
        Preserve attributes from the original queryset.

        This enables composition with other queryset enhancements like
        queryable properties, annotations, etc.
        """
        # Copy non-method attributes that might be set by other managers
        for attr_name in dir(original_qs):
            if not attr_name.startswith("_") and not hasattr(cls, attr_name) and not callable(getattr(original_qs, attr_name, None)):
                try:
                    value = getattr(original_qs, attr_name)
                    setattr(hook_qs, attr_name, value)
                except (AttributeError, TypeError):
                    # Skip attributes that can't be copied
                    continue

    @property
    def coordinator(self):
        """Lazy initialization of coordinator"""
        if self._coordinator is None:
            from django_bulk_hooks.operations import BulkOperationCoordinator

            self._coordinator = BulkOperationCoordinator(self)
        return self._coordinator

    def _use_intent_architecture(self) -> bool:
        config = getattr(settings, "DJANGO_BULK_HOOKS", {})
        return bool(config.get("USE_INTENT_ARCHITECTURE", False))

    @transaction.atomic
    def bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
        bypass_hooks=False,
    ):
        """
        Create multiple objects with hook support.

        This is the public API - delegates to coordinator.
        """
        if self._use_intent_architecture():
            return self._bulk_create_v3(
                objs=objs,
                batch_size=batch_size,
                ignore_conflicts=ignore_conflicts,
                update_conflicts=update_conflicts,
                update_fields=update_fields,
                unique_fields=unique_fields,
                bypass_hooks=bypass_hooks,
            )
        return self.coordinator.create(
            objs=objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
            bypass_hooks=bypass_hooks,
        )

    @transaction.atomic
    def bulk_update(
        self,
        objs,
        fields=None,
        batch_size=None,
        bypass_hooks=False,
        **kwargs,
    ):
        """
        Update multiple objects with hook support.

        This is the public API - delegates to coordinator.

        Args:
            objs: List of model instances to update
            fields: List of field names to update (optional, will auto-detect if None)
            batch_size: Number of objects per batch
            bypass_hooks: Skip all hooks if True

        Returns:
            Number of objects updated
        """
        # DEBUG: Log incoming fields parameter
        logger.debug(f"🟦 QUERYSET.bulk_update ENTRY: fields={fields}, objs count={len(objs) if objs else 0}")

        # If fields is None, auto-detect changed fields using analyzer
        if fields is None:
            from django_bulk_hooks.operations.analyzer import ModelAnalyzer

            fields = ModelAnalyzer(self.model).detect_changed_fields(objs)
            logger.debug(f"🟦 QUERYSET.bulk_update: Auto-detected fields={fields}")
            if not fields:
                return 0

        if self._use_intent_architecture():
            return self._bulk_update_v3(
                objs=objs,
                fields=fields,
                batch_size=batch_size,
                bypass_hooks=bypass_hooks,
            )

        logger.debug(f"🟦 QUERYSET.bulk_update: Calling coordinator.update with fields={fields}")
        return self.coordinator.update(
            objs=objs,
            fields=fields,
            batch_size=batch_size,
            bypass_hooks=bypass_hooks,
        )

    @transaction.atomic
    def update(self, bypass_hooks=False, **kwargs):
        """
        Update QuerySet with hook support.

        This is the public API - delegates to coordinator.

        Args:
            bypass_hooks: Skip all hooks if True
            **kwargs: Fields to update

        Returns:
            Number of objects updated
        """
        if self._use_intent_architecture():
            return self._update_v3(update_kwargs=kwargs, bypass_hooks=bypass_hooks)
        return self.coordinator.update_queryset(
            update_kwargs=kwargs,
            bypass_hooks=bypass_hooks,
        )

    @transaction.atomic
    def bulk_delete(
        self,
        objs,
        bypass_hooks=False,
        **kwargs,
    ):
        """
        Delete multiple objects with hook support.

        This is the public API - delegates to coordinator.

        Args:
            objs: List of objects to delete
            bypass_hooks: Skip all hooks if True

        Returns:
            Tuple of (count, details dict)
        """
        if self._use_intent_architecture():
            return self._bulk_delete_v3(objs=objs, bypass_hooks=bypass_hooks)

        # Filter queryset to only these objects
        pks = extract_pks(objs)
        if not pks:
            return 0

        # Create a filtered queryset
        filtered_qs = self.filter(pk__in=pks)

        # Use coordinator with the filtered queryset
        from django_bulk_hooks.operations import BulkOperationCoordinator

        coordinator = BulkOperationCoordinator(filtered_qs)

        count, details = coordinator.delete(
            bypass_hooks=bypass_hooks,
        )

        # For bulk_delete, return just the count to match Django's behavior
        return count

    @transaction.atomic
    def delete(self, bypass_hooks=False):
        """
        Delete QuerySet with hook support.

        This is the public API - delegates to coordinator.

        Args:
            bypass_hooks: Skip all hooks if True

        Returns:
            Tuple of (count, details dict)
        """
        if self._use_intent_architecture():
            return self._delete_v3(bypass_hooks=bypass_hooks)
        return self.coordinator.delete(
            bypass_hooks=bypass_hooks,
        )

    # ==================== Intent-centric v3 API ====================

    def _bulk_create_v3(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
        bypass_hooks=False,
    ):
        if not objs:
            return objs

        from django_bulk_hooks.core.context import OperationContext
        from django_bulk_hooks.core.intent import IntentBuilder
        from django_bulk_hooks.orchestration.orchestrator import get_orchestrator

        intent_builder = (
            IntentBuilder(self.model)
            .for_create()
            .with_unique_fields(unique_fields)
            .with_options(
                batch_size=batch_size,
                ignore_conflicts=ignore_conflicts,
                update_conflicts=update_conflicts,
                bypass_hooks=bypass_hooks,
                using_db=self.db,
            )
        )
        if update_fields is not None:
            intent_builder = intent_builder.with_update_fields(update_fields)
        intent = intent_builder.build()
        context = OperationContext(intent).with_instances(new_records=tuple(objs))

        return get_orchestrator().execute_create(context, objs)

    def _bulk_update_v3(
        self,
        objs,
        fields,
        batch_size=None,
        bypass_hooks=False,
    ):
        if not objs or not fields:
            return 0

        from django_bulk_hooks.core.context import OperationContext
        from django_bulk_hooks.core.intent import IntentBuilder
        from django_bulk_hooks.orchestration.orchestrator import get_orchestrator

        pks = tuple(obj.pk for obj in objs if obj.pk is not None)
        intent = (
            IntentBuilder(self.model)
            .for_update()
            .targeting(pks)
            .with_update_fields(fields)
            .with_options(
                batch_size=batch_size,
                bypass_hooks=bypass_hooks,
                using_db=self.db,
            )
            .build()
        )
        context = OperationContext(intent).with_instances(new_records=tuple(objs))
        return get_orchestrator().execute_update(context, objs, fields)

    def _update_v3(self, update_kwargs, bypass_hooks=False):
        if not update_kwargs:
            return 0

        from django_bulk_hooks.core.context import OperationContext
        from django_bulk_hooks.core.intent import IntentBuilder
        from django_bulk_hooks.orchestration.orchestrator import get_orchestrator

        pks = tuple(self.values_list("pk", flat=True))
        if not pks:
            return 0

        intent = (
            IntentBuilder(self.model)
            .for_update()
            .targeting(pks)
            .setting(**update_kwargs)
            .with_options(
                bypass_hooks=bypass_hooks,
                using_db=self.db,
            )
            .build()
        )
        context = OperationContext(intent)
        return get_orchestrator().execute_queryset_update(context, self, update_kwargs)

    def _delete_v3(self, bypass_hooks=False):
        from django_bulk_hooks.core.context import OperationContext
        from django_bulk_hooks.core.intent import IntentBuilder
        from django_bulk_hooks.orchestration.orchestrator import get_orchestrator

        pks = tuple(self.values_list("pk", flat=True))
        if not pks:
            return (0, {})

        intent = (
            IntentBuilder(self.model)
            .for_delete()
            .targeting(pks)
            .with_options(
                bypass_hooks=bypass_hooks,
                using_db=self.db,
            )
            .build()
        )
        context = OperationContext(intent)
        return get_orchestrator().execute_delete(context, self)

    def _bulk_delete_v3(self, objs, bypass_hooks=False):
        pks = extract_pks(objs)
        if not pks:
            return 0

        filtered_qs = HookQuerySet.with_hooks(self.filter(pk__in=pks))
        count, _details = filtered_qs._delete_v3(bypass_hooks=bypass_hooks)
        return count
