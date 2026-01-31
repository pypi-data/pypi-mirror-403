import logging
from typing import List

from django.db.models import Model, QuerySet

from django_bulk_hooks.core.context import OperationContext
from django_bulk_hooks.operations.field_utils import handle_auto_now_fields

logger = logging.getLogger(__name__)


class DatabaseExecutor:
    """
    Execute database operations with no hook logic.
    """

    def bulk_create(self, context: OperationContext, objs: List[Model]) -> List[Model]:
        intent = context.intent
        qs = intent.model_cls._base_manager.all()
        if intent.using_db:
            qs = qs.using(intent.using_db)

        update_fields = list(intent.update_fields) if intent.update_fields else None
        if intent.update_conflicts and update_fields:
            update_fields = self._remove_auto_now_add_fields(update_fields, objs)

        return qs.bulk_create(
            objs,
            batch_size=intent.batch_size,
            ignore_conflicts=intent.ignore_conflicts,
            update_conflicts=intent.update_conflicts,
            update_fields=update_fields,
            unique_fields=list(intent.unique_fields) if intent.unique_fields else None,
        )

    def bulk_update(
        self,
        context: OperationContext,
        objs: List[Model],
        fields: List[str],
    ) -> int:
        intent = context.intent
        qs = intent.model_cls._base_manager.all()
        if intent.using_db:
            qs = qs.using(intent.using_db)
        if not objs:
            return 0

        fields = self._add_auto_now_fields(fields, objs)
        fields = self._remove_auto_now_add_fields(fields, objs)
        return qs.bulk_update(objs, fields, batch_size=intent.batch_size)

    def queryset_update(self, queryset: QuerySet, **kwargs) -> int:
        return QuerySet.update(queryset, **kwargs)

    def queryset_delete(self, queryset: QuerySet):
        return QuerySet.delete(queryset)

    def _add_auto_now_fields(self, fields: List[str], objs: List[Model]) -> List[str]:
        if not objs:
            return fields
        auto_now_fields = handle_auto_now_fields(objs[0].__class__, objs, for_update=True)
        for field_name in auto_now_fields:
            if field_name not in fields:
                fields.append(field_name)
        return fields

    def _remove_auto_now_add_fields(self, fields: List[str], objs: List[Model]) -> List[str]:
        if not objs:
            return fields
        model_cls = objs[0].__class__
        auto_now_add_fields = set()
        for field in model_cls._meta.get_fields():
            if getattr(field, "auto_now_add", False):
                auto_now_add_fields.add(field.name)
        if not auto_now_add_fields:
            return fields
        filtered = [field for field in fields if field not in auto_now_add_fields]
        removed = auto_now_add_fields.intersection(fields)
        if removed:
            logger.info(
                "Removed auto_now_add fields from update fields list: %s",
                ", ".join(sorted(removed)),
            )
        return filtered
