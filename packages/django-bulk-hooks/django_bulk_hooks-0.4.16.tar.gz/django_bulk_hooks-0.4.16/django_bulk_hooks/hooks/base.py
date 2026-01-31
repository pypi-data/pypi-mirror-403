import logging

from django_bulk_hooks.enums import DEFAULT_PRIORITY
from django_bulk_hooks.registry import register_hook, unregister_hook

from .requirements import HookRequirements

logger = logging.getLogger(__name__)


class HookMeta(type):
    _registered = set()
    _class_hook_map: dict[type, set[tuple]] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        mcs._register_hooks_for_class(cls)
        return cls

    @classmethod
    def _register_hooks_for_class(mcs, cls):
        # Unregister parent hooks to ensure overrides win
        for base in cls.__mro__[1:]:
            if not isinstance(base, HookMeta):
                continue
            if base in mcs._class_hook_map:
                for model_cls, event, base_cls, method_name in list(
                    mcs._class_hook_map[base],
                ):
                    key = (model_cls, event, base_cls, method_name)
                    if key in HookMeta._registered:
                        unregister_hook(model_cls, event, base_cls, method_name)
                        HookMeta._registered.discard(key)

        all_hook_methods = {}
        for klass in reversed(cls.__mro__):
            if not isinstance(klass, HookMeta):
                continue
            for method_name, method in klass.__dict__.items():
                if hasattr(method, "_hook_registrations"):
                    all_hook_methods[method_name] = method

        if cls not in mcs._class_hook_map:
            mcs._class_hook_map[cls] = set()

        for method_name, method in all_hook_methods.items():
            for reg in getattr(method, "_hook_registrations", []):
                model_cls = reg["model"]
                event = reg["event"]
                condition = reg.get("condition")
                priority = reg.get("priority", DEFAULT_PRIORITY)
                key = (model_cls, event, cls, method_name)
                if key in HookMeta._registered:
                    continue
                register_hook(
                    model=model_cls,
                    event=event,
                    handler_cls=cls,
                    method_name=method_name,
                    condition=condition,
                    priority=priority,
                )
                HookMeta._registered.add(key)
                mcs._class_hook_map[cls].add(key)


class Hook(metaclass=HookMeta):
    """
    Base class for hook handlers with declarative requirements.
    """

    requirements: HookRequirements = HookRequirements.standard()

    def get_requirements(self, event: str) -> HookRequirements:
        return self.requirements
