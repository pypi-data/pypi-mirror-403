import inspect
import logging

from django_bulk_hooks.core.changeset import RecordChange
from django_bulk_hooks.core.context import OperationContext

logger = logging.getLogger(__name__)


class SignatureAdapter:
    """
    Adapter for hook method signatures.
    """

    @staticmethod
    def call_hook(method, context: OperationContext) -> None:
        sig = inspect.signature(method)
        params = [p for p in sig.parameters.values() if p.name != "self"]
        names = [p.name for p in params]

        if "ctx" in names or "context" in names:
            return method(context)

        changeset = context.changeset
        new_records = changeset.new_records
        old_records = changeset.old_records

        if all(name in {"changeset", "new_records", "old_records"} for name in names):
            positional = []
            for name in names:
                if name == "changeset":
                    positional.append(changeset)
                elif name == "new_records":
                    positional.append(new_records)
                elif name == "old_records":
                    positional.append(old_records)
            return method(*positional)

        kwargs = {}
        if "changeset" in names:
            kwargs["changeset"] = changeset
        if "new_records" in names:
            kwargs["new_records"] = new_records
        if "old_records" in names:
            kwargs["old_records"] = old_records

        if kwargs:
            return method(**kwargs)

        return method()


class ConditionAdapter:
    """
    Adapter for condition signatures.
    """

    @staticmethod
    def check(condition, record: RecordChange, context: OperationContext) -> bool:
        condition_name = condition.__class__.__name__
        
        # Get field name if available for logging
        field_name = getattr(condition, 'field', None)
        pk = record.pk
        
        logger.debug(
            "[CONDITION] Evaluating %s(field=%s) for record pk=%s",
            condition_name,
            field_name,
            pk,
        )
        
        sig = inspect.signature(condition.check)
        if "context" in sig.parameters:
            # New signature with context
            logger.debug("[CONDITION] Using new signature (with context)")
            result = condition.check(record, context)
        else:
            # Old signature without context
            logger.debug("[CONDITION] Using legacy signature (without context)")
            try:
                result = condition.check(record.new_record, record.old_record)
            except TypeError:
                result = condition.check(record.new_record)
        
        # Log detailed information for specific conditions
        if field_name and hasattr(record, 'get_new_value'):
            new_val = record.get_new_value(field_name)
            old_val = record.get_old_value(field_name) if record.old_record else None
            in_scope = context.is_field_in_scope(field_name)
            
            logger.info(
                "[CONDITION] %s(field=%s): pk=%s, result=%s, in_scope=%s, old=%s, new=%s",
                condition_name,
                field_name,
                pk,
                result,
                in_scope,
                old_val,
                new_val,
            )
        else:
            logger.debug("[CONDITION] %s: pk=%s, result=%s", condition_name, pk, result)
        
        return result
