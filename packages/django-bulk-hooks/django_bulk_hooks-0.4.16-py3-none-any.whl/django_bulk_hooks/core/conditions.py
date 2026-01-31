from __future__ import annotations

from typing import Any

from .changeset import RecordChange
from .context import OperationContext


class HookCondition:
    """
    Base class for hook conditions with context-aware signature.
    """

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        raise NotImplementedError

    def __call__(self, record: RecordChange, context: OperationContext) -> bool:
        return self.check(record, context)

    def __and__(self, other: "HookCondition") -> "HookCondition":
        return _AndCondition(self, other)

    def __or__(self, other: "HookCondition") -> "HookCondition":
        return _OrCondition(self, other)

    def __invert__(self) -> "HookCondition":
        return _NotCondition(self)


class HasChanged(HookCondition):
    def __init__(self, field: str, has_changed: bool = True):
        self.field = field
        self.has_changed = has_changed

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        # CREATE operations don't "change" anything - they create new records
        # This prevents HasChanged from firing during bulk_create with update_conflicts
        if context.operation_type == "create":
            return not self.has_changed

        if not context.is_field_in_scope(self.field):
            return not self.has_changed
        actual_changed = record.has_changed(self.field)
        return actual_changed == self.has_changed


class IsEqual(HookCondition):
    def __init__(self, field: str, value: Any, only_on_change: bool = False):
        self.field = field
        self.value = value
        self.only_on_change = only_on_change

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        current = record.get_new_value(self.field)
        if self.only_on_change:
            if record.old_record is None:
                return False
            previous = record.get_old_value(self.field)
            return previous != self.value and current == self.value
        return current == self.value


class ChangesTo(HookCondition):
    def __init__(self, field: str, value: Any):
        self.field = field
        self.value = value

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        if not context.is_field_in_scope(self.field):
            return False
        if record.old_record is None:
            return False
        previous = record.get_old_value(self.field)
        current = record.get_new_value(self.field)
        return previous != self.value and current == self.value


class ChangesFrom(HookCondition):
    def __init__(self, field: str, value: Any):
        self.field = field
        self.value = value

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        if not context.is_field_in_scope(self.field):
            return False
        if record.old_record is None:
            return False
        previous = record.get_old_value(self.field)
        current = record.get_new_value(self.field)
        return previous == self.value and current != self.value


class _AndCondition(HookCondition):
    def __init__(self, left: HookCondition, right: HookCondition):
        self.left = left
        self.right = right

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        return self.left.check(record, context) and self.right.check(record, context)


class _OrCondition(HookCondition):
    def __init__(self, left: HookCondition, right: HookCondition):
        self.left = left
        self.right = right

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        return self.left.check(record, context) or self.right.check(record, context)


class _NotCondition(HookCondition):
    def __init__(self, condition: HookCondition):
        self.condition = condition

    def check(self, record: RecordChange, context: OperationContext) -> bool:
        return not self.condition.check(record, context)
