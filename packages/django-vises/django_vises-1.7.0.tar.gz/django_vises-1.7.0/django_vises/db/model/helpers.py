from typing import Any

from django.db.models import Model


def get_model_fields(model: type[Model]) -> list[str]:
    return [field.name for field in model._meta.get_fields()]


def convert_model_object_to_dict(model: Model) -> dict[str, Any]:
    return {
        field.name: getattr(model, field.name) for field in model._meta.get_fields()
    }
