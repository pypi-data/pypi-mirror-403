from typing import Optional

from django.db import models

from django_bulk_hooks.enums import DEFAULT_PRIORITY


def hook(
    model: type[models.Model],
    event: str,
    when: Optional[object] = None,
    priority: int = DEFAULT_PRIORITY,
):
    """
    Decorator to register a hook method on a handler class.
    """

    def decorator(method):
        if not hasattr(method, "_hook_registrations"):
            method._hook_registrations = []
        method._hook_registrations.append(
            {
                "model": model,
                "event": event,
                "condition": when,
                "priority": priority,
            }
        )
        return method

    return decorator
