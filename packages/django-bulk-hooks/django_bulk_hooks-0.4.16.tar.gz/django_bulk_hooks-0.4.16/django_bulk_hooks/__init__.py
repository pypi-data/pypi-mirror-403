"""
Django Bulk Hooks - Salesforce-style hooks for Django bulk operations.

Architecture:
    Following Salesforce's trigger context pattern, each bulk operation
    gets an isolated dispatcher context that's automatically cleaned up.
    This prevents memory leaks in long-lived processes (web servers).
"""

import logging

from django_bulk_hooks.changeset import ChangeSet
from django_bulk_hooks.changeset import RecordChange
from django_bulk_hooks.constants import DEFAULT_BULK_UPDATE_BATCH_SIZE
from django_bulk_hooks.dispatcher import HookDispatcher
from django_bulk_hooks.factory import clear_hook_factories
from django_bulk_hooks.factory import configure_hook_container
from django_bulk_hooks.factory import configure_nested_container
from django_bulk_hooks.factory import create_hook_instance
from django_bulk_hooks.factory import dishka_hook_resolver
from django_bulk_hooks.factory import is_container_configured
from django_bulk_hooks.factory import set_default_hook_factory
from django_bulk_hooks.factory import set_hook_factory
from django_bulk_hooks.conditions import when
from django_bulk_hooks.graph import Context
from django_bulk_hooks.graph import DependencyGraph
from django_bulk_hooks.graph import Step
from django_bulk_hooks.graph import Workflow
from django_bulk_hooks.helpers import get_changed_fields
from django_bulk_hooks.decorators import (
    after_create,
    after_delete,
    after_update,
    before_create,
    before_delete,
    before_update,
    hook,
    prefetch_related,
    select_related,
    validate_create,
    validate_delete,
    validate_update,
)
from django_bulk_hooks.handler import Hook

# Backward compatibility alias
HookClass = Hook
from django_bulk_hooks.helpers import build_changeset_for_create
from django_bulk_hooks.helpers import build_changeset_for_delete
from django_bulk_hooks.helpers import build_changeset_for_update
from django_bulk_hooks.helpers import dispatch_hooks_for_operation
from django_bulk_hooks.manager import BulkHookManager
from django_bulk_hooks.operations import BulkExecutor
from django_bulk_hooks.core import IntentBuilder
from django_bulk_hooks.core import OperationContext
from django_bulk_hooks.core import OperationIntent
from django_bulk_hooks.hooks import Hook as IntentHook
from django_bulk_hooks.hooks import HookRequirements
from django_bulk_hooks.hooks import hook as intent_hook

# Service layer (composition-based architecture)
from django_bulk_hooks.operations import BulkOperationCoordinator
from django_bulk_hooks.operations import ModelAnalyzer

__all__ = [
    # Manager and Hook base class
    "BulkHookManager",
    "Hook",
    "HookClass",  # Backward compatibility alias
    # Event-specific decorators (Salesforce-style)
    "after_create",
    "after_delete",
    "after_update",
    "before_create",
    "before_delete",
    "before_update",
    "validate_create",
    "validate_delete",
    "validate_update",
    # Legacy decorators (backward compatibility)
    "hook",
    "prefetch_related",
    "select_related",
    # Fluent condition builder
    "when",
    # Dependency graph (run_for_changes, per-record gating)
    "DependencyGraph",
    "Workflow",
    "Step",
    "Context",
    "get_changed_fields",
    # Dependency injection
    "set_hook_factory",
    "set_default_hook_factory",
    "configure_hook_container",
    "configure_nested_container",
    "dishka_hook_resolver",
    "clear_hook_factories",
    "create_hook_instance",
    "is_container_configured",
    # Constants
    "DEFAULT_BULK_UPDATE_BATCH_SIZE",
    # Changeset (Salesforce-style context)
    "ChangeSet",
    "RecordChange",
    "build_changeset_for_create",
    "build_changeset_for_update",
    "build_changeset_for_delete",
    # Dispatcher (per-operation context)
    "HookDispatcher",
    "dispatch_hooks_for_operation",
    # Service layer (composition-based architecture)
    "BulkOperationCoordinator",
    "ModelAnalyzer",
    "BulkExecutor",
    # Intent-centric core
    "OperationIntent",
    "IntentBuilder",
    "OperationContext",
    # Intent-centric hooks
    "IntentHook",
    "HookRequirements",
    "intent_hook",
]
