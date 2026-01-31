import logging
from typing import List, Optional

from django_bulk_hooks.core.changeset import ChangeSet, RecordChange
from django_bulk_hooks.core.context import OperationContext
from django_bulk_hooks.factory import create_hook_instance
from django_bulk_hooks.hooks.adapters import ConditionAdapter, SignatureAdapter

logger = logging.getLogger(__name__)


class HookDispatcher:
    """
    Dispatch hooks based on conditions and priority.
    """

    def __init__(self, registry):
        self.registry = registry

    def dispatch(self, context: OperationContext, event: str) -> None:
        hooks = self._get_hooks(context.model_cls, event)
        if not hooks:
            return

        logger.info(
            "Dispatching %s for %s: %d hooks",
            event,
            context.model_cls.__name__,
            len(hooks),
        )

        for handler_cls, method_name, condition, priority in hooks:
            self._execute_hook(handler_cls, method_name, condition, context, event)

    def _get_hooks(self, model_cls: type, event: str):
        try:
            hooks = self.registry.get_hooks_including_abstract(model_cls, event)
        except Exception:
            hooks = []
        if not hooks:
            hooks = self.registry.get_hooks(model_cls, event)
        return hooks

    def _execute_hook(
        self,
        handler_cls: type,
        method_name: str,
        condition: Optional[object],
        context: OperationContext,
        event: str,
    ) -> None:
        logger.info(
            "[DISPATCHER] Evaluating hook: %s.%s for event=%s, model=%s",
            handler_cls.__name__,
            method_name,
            event,
            context.model_cls.__name__,
        )
        
        filtered_context = context
        if condition is not None:
            logger.debug(
                "[DISPATCHER] Evaluating condition: %s (total records: %d)",
                condition.__class__.__name__,
                len(context.changeset),
            )
            matching_changes = [
                change
                for change in context.changeset
                if ConditionAdapter.check(condition, change, context)
            ]
            if not matching_changes:
                logger.debug(
                    "[DISPATCHER]   → %s.%s: no matching records (condition filtered all)",
                    handler_cls.__name__,
                    method_name,
                )
                return
            logger.info(
                "[DISPATCHER]   → Condition matched %d/%d records",
                len(matching_changes),
                len(context.changeset),
            )
            filtered_context = _FilteredContext(context, matching_changes)
        else:
            logger.debug("[DISPATCHER]   → No condition, all records match")

        logger.info(
            "[DISPATCHER] Executing hook: %s.%s with %d records",
            handler_cls.__name__,
            method_name,
            len(filtered_context.changeset),
        )
        handler = create_hook_instance(handler_cls)
        method = getattr(handler, method_name)
        SignatureAdapter.call_hook(method, filtered_context)
        logger.info("[DISPATCHER] Hook completed: %s.%s", handler_cls.__name__, method_name)


class _FilteredContext:
    """
    Lightweight wrapper to expose a filtered ChangeSet.
    """

    def __init__(self, base: OperationContext, changes: List[RecordChange]):
        self._base = base
        self._changeset = ChangeSet(base, tuple(changes))

    @property
    def intent(self):
        return self._base.intent

    @property
    def changeset(self):
        return self._changeset

    @property
    def operation_type(self) -> str:
        return self._base.operation_type

    @property
    def model_cls(self) -> type:
        return self._base.model_cls

    @property
    def operation_id(self):
        return self._base.operation_id

    def is_field_in_scope(self, field_name: str) -> bool:
        return self._base.is_field_in_scope(field_name)

    @property
    def old_records_map(self):
        return self._base.old_records_map

    @property
    def new_records(self):
        return tuple(self._changeset.new_records)
