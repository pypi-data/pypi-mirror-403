import logging
from typing import Any, Dict, List, Tuple

from django.db.models import Model, QuerySet

from django_bulk_hooks.core.context import OperationContext
from django_bulk_hooks.factory import create_hook_instance
from django_bulk_hooks.hooks.requirements import HookRequirements
from django_bulk_hooks.registry import get_registry

from .dispatcher import HookDispatcher
from .executor import DatabaseExecutor

logger = logging.getLogger(__name__)


class HookOrchestrator:
    """
    Manage hook lifecycle for operations.
    """

    def __init__(self, dispatcher: HookDispatcher, executor: DatabaseExecutor):
        self.dispatcher = dispatcher
        self.executor = executor

    def execute_create(self, context: OperationContext, objs: List[Model]) -> List[Model]:
        if context.intent.bypass_hooks:
            return self.executor.bulk_create(context, objs)

        logger.info(
            "[ORCHESTRATOR] execute_create started: model=%s, count=%d, operation_id=%s",
            context.model_cls.__name__,
            len(objs),
            context.operation_id,
        )

        requirements = self._aggregate_requirements(context, "create")
        logger.debug(
            "[ORCHESTRATOR] Requirements aggregated: old_records=%s, new_records=%s, preload=%s",
            requirements.old_records,
            requirements.new_records,
            requirements.preload_related,
        )
        context = self._apply_requirements(context, requirements)

        logger.debug("[ORCHESTRATOR] Dispatching validate_create")
        self.dispatcher.dispatch(context, "validate_create")

        logger.debug("[ORCHESTRATOR] Dispatching before_create")
        self.dispatcher.dispatch(context, "before_create")

        logger.debug("[ORCHESTRATOR] Executing database bulk_create")
        result = self.executor.bulk_create(context, objs)
        logger.debug("[ORCHESTRATOR] Database bulk_create completed, %d records created", len(result))

        context = context.with_instances(new_records=tuple(result))

        logger.debug("[ORCHESTRATOR] Dispatching after_create")
        self.dispatcher.dispatch(context, "after_create")

        logger.info("[ORCHESTRATOR] execute_create completed: model=%s", context.model_cls.__name__)
        return result

    def execute_update(
        self,
        context: OperationContext,
        objs: List[Model],
        fields: List[str],
    ) -> int:
        if context.intent.bypass_hooks:
            return self.executor.bulk_update(context, objs, fields)

        logger.info(
            "[ORCHESTRATOR] execute_update started: model=%s, count=%d, fields=%s, operation_id=%s",
            context.model_cls.__name__,
            len(objs),
            fields,
            context.operation_id,
        )

        requirements = self._aggregate_requirements(context, "update")
        logger.debug(
            "[ORCHESTRATOR] Requirements aggregated: old_records=%s, new_records=%s",
            requirements.old_records,
            requirements.new_records,
        )
        context = self._apply_requirements(context, requirements)

        old_records_map = None
        if requirements.old_records:
            logger.debug("[ORCHESTRATOR] Loading old_records_map")
            old_records_map = context.old_records_map

        logger.debug("[ORCHESTRATOR] Dispatching validate_update")
        self.dispatcher.dispatch(context, "validate_update")

        logger.debug("[ORCHESTRATOR] Dispatching before_update")
        self.dispatcher.dispatch(context, "before_update")

        logger.debug("[ORCHESTRATOR] Executing database bulk_update")
        count = self.executor.bulk_update(context, objs, fields)
        logger.debug("[ORCHESTRATOR] Database bulk_update completed, %d records updated", count)

        self._log_bulk_update_sample(context, fields)

        context.clear_caches()
        if old_records_map is not None:
            context = context.with_instances(old_records_map=old_records_map)

        logger.debug("[ORCHESTRATOR] Dispatching after_update")
        self.dispatcher.dispatch(context, "after_update")

        logger.info("[ORCHESTRATOR] execute_update completed: model=%s", context.model_cls.__name__)
        return count

    def _log_bulk_update_sample(
        self,
        context: OperationContext,
        fields: List[str],
        sample_size: int = 5,
    ) -> None:
        if not logger.isEnabledFor(logging.DEBUG):
            return

        if not fields:
            logger.debug("[ORCHESTRATOR] bulk_update sample: no fields to compare")
            return

        old_records_map = context.old_records_map
        new_records = context.new_records
        if not new_records:
            logger.debug("[ORCHESTRATOR] bulk_update sample: no new records loaded")
            return

        sample = new_records[: min(sample_size, len(new_records))]
        logger.debug(
            "[ORCHESTRATOR] bulk_update sample: fields=%s, sample_size=%d",
            fields,
            len(sample),
        )

        for instance in sample:
            old_instance = old_records_map.get(instance.pk)
            if old_instance is None:
                logger.debug(
                    "[ORCHESTRATOR] bulk_update sample: pk=%s old instance missing",
                    instance.pk,
                )
                continue

            old_values = {
                field: self._safe_field_value(old_instance, field, context.model_cls)
                for field in fields
            }
            new_values = {
                field: self._safe_field_value(instance, field, context.model_cls)
                for field in fields
            }
            logger.debug(
                "[ORCHESTRATOR] bulk_update sample: pk=%s old=%s new=%s",
                instance.pk,
                old_values,
                new_values,
            )

    def _safe_field_value(self, instance: Model, field_name: str, model_cls: type) -> Any:
        try:
            field = model_cls._meta.get_field(field_name)
        except Exception:
            return getattr(instance, field_name, None)

        if field.is_relation and not field.many_to_many:
            return getattr(instance, field.attname, None)

        return getattr(instance, field.name, None)

    def execute_queryset_update(
        self,
        context: OperationContext,
        queryset: QuerySet,
        kwargs: Dict[str, Any],
    ) -> int:
        if context.intent.bypass_hooks:
            return self.executor.queryset_update(queryset, **kwargs)

        requirements = self._aggregate_requirements(context, "update")
        context = self._apply_requirements(context, requirements)

        old_records_map = None
        if requirements.old_records:
            old_records_map = context.old_records_map

        self.dispatcher.dispatch(context, "validate_update")
        self.dispatcher.dispatch(context, "before_update")

        count = self.executor.queryset_update(queryset, **kwargs)
        if count == 0:
            return 0

        context.clear_caches()
        if old_records_map is not None:
            context = context.with_instances(old_records_map=old_records_map)
        self.dispatcher.dispatch(context, "after_update")
        return count

    def execute_delete(
        self,
        context: OperationContext,
        queryset: QuerySet,
    ) -> Tuple[int, Dict[str, int]]:
        if context.intent.bypass_hooks:
            return self.executor.queryset_delete(queryset)

        requirements = self._aggregate_requirements(context, "delete")
        context = self._apply_requirements(context, requirements)

        _ = context.old_records_map

        self.dispatcher.dispatch(context, "validate_delete")
        self.dispatcher.dispatch(context, "before_delete")

        result = self.executor.queryset_delete(queryset)
        self.dispatcher.dispatch(context, "after_delete")
        return result

    def _aggregate_requirements(
        self,
        context: OperationContext,
        operation_type: str,
    ) -> HookRequirements:
        events = [
            f"validate_{operation_type}",
            f"before_{operation_type}",
            f"after_{operation_type}",
        ]

        needs_old = False
        needs_new = False
        preload_related = set()
        prefetch_related = set()

        for event in events:
            # CRITICAL: Must use get_hooks_including_abstract to find hooks on abstract models
            hooks = self.dispatcher.registry.get_hooks_including_abstract(context.model_cls, event)

            logger.debug(
                "[ORCHESTRATOR] Aggregating requirements for %s.%s: found %d hooks",
                context.model_cls.__name__,
                event,
                len(hooks),
            )

            if operation_type == "update" and hooks:
                logger.debug(
                    "[ORCHESTRATOR]   Salesforce-style default: enabling old_records for update hooks",
                )
                needs_old = True

            # Smart default: if there are any after_update hooks, load old_records for comparisons
            if event == f"after_{operation_type}" and operation_type in ("update", "delete") and hooks:
                logger.debug(
                    "[ORCHESTRATOR]   Smart default: enabling old_records for %s hooks (needed for comparisons)",
                    event,
                )
                needs_old = True

            for handler_cls, method_name, condition, priority in hooks:
                handler = create_hook_instance(handler_cls)

                # Get requirements - backward compatible with hooks that don't have this method
                if hasattr(handler, "get_requirements"):
                    reqs = handler.get_requirements(event)
                elif hasattr(handler_cls, "requirements"):
                    # Try to get from class attribute
                    reqs = handler_cls.requirements
                else:
                    # Default requirements for legacy hooks
                    reqs = HookRequirements.standard()

                # Extract @select_related and @prefetch_related from decorator metadata
                try:
                    method = getattr(handler_cls, method_name, None)
                    if method:
                        # Extract @select_related fields
                        select_related_fields = getattr(method, "_select_related_fields", None)
                        if select_related_fields and hasattr(select_related_fields, "__iter__"):
                            logger.debug(
                                "[ORCHESTRATOR]   Extracting @select_related from %s.%s: %s",
                                handler_cls.__name__,
                                method_name,
                                list(select_related_fields),
                            )
                            preload_related.update(select_related_fields)
                        
                        # Extract @prefetch_related fields
                        prefetch_related_fields = getattr(method, "_prefetch_related_fields", None)
                        if prefetch_related_fields and hasattr(prefetch_related_fields, "__iter__"):
                            logger.debug(
                                "[ORCHESTRATOR]   Extracting @prefetch_related from %s.%s: %s",
                                handler_cls.__name__,
                                method_name,
                                list(prefetch_related_fields),
                            )
                            prefetch_related.update(prefetch_related_fields)
                except Exception as e:
                    logger.warning(
                        "Failed to extract decorator metadata from %s.%s: %s",
                        handler_cls.__name__,
                        method_name,
                        e,
                    )

                logger.debug(
                    "[ORCHESTRATOR]   Hook %s.%s requires: old=%s, new=%s",
                    handler_cls.__name__,
                    method_name,
                    reqs.old_records,
                    reqs.new_records,
                )

                needs_old = needs_old or reqs.old_records
                needs_new = needs_new or reqs.new_records
                preload_related.update(reqs.preload_related)
                prefetch_related.update(reqs.prefetch_related)

        return HookRequirements(
            old_records=needs_old,
            new_records=needs_new,
            preload_related=frozenset(preload_related),
            prefetch_related=frozenset(prefetch_related),
        )

    def _apply_requirements(
        self,
        context: OperationContext,
        requirements: HookRequirements,
    ) -> OperationContext:
        if requirements.preload_related:
            context = context.with_preloaded_relations(requirements.preload_related)
        if requirements.prefetch_related:
            context = context.with_prefetched_relations(requirements.prefetch_related)
        return context


_orchestrator: HookOrchestrator | None = None


def get_orchestrator() -> HookOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HookOrchestrator(
            dispatcher=HookDispatcher(get_registry()),
            executor=DatabaseExecutor(),
        )
    return _orchestrator
