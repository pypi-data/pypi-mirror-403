from typing import Any, Iterable


class DataMixin:
    model: Any  # type: ignore[assignment]

    def _from_data(self, data: Iterable[Any]) -> list[Any]:
        converted: list[Any] = []
        model = getattr(self, "model", None)
        if model is None:
            return converted
        for item in data:
            if isinstance(item, model):
                converted.append(item)
            elif isinstance(item, dict):
                obj = self._dict_to_model(item)
                converted.append(obj)
            else:
                obj = self._object_to_model(item)
                converted.append(obj)
        return converted

    def _dict_to_model(self, data: dict) -> Any:
        model = getattr(self, "model", None)
        if model is None:
            return None
        model_field_names = {field.name for field in model._meta.fields}
        obj = model()
        for field_name in model_field_names:
            if field_name in data:
                setattr(obj, field_name, data[field_name])
        return obj

    def _object_to_model(self, obj: Any) -> Any:
        model = getattr(self, "model", None)
        if model is None:
            return None
        model_field_names = {field.name for field in model._meta.fields}
        model_obj = model()
        for field_name in model_field_names:
            if hasattr(obj, field_name):
                value = getattr(obj, field_name)
                if callable(value):
                    setattr(model_obj, field_name, value())
                else:
                    setattr(model_obj, field_name, value)
        return model_obj
