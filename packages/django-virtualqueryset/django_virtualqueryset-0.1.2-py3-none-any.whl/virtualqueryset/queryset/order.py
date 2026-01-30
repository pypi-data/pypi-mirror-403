class OrderMixin:
    def _get_field_value(self, obj, field_name):
        value = getattr(obj, field_name, None)
        if value is None:
            return ""
        if isinstance(value, str):
            return value.lower()
        return value

    def order_by(self, *fields):
        rslt = list(self._result_cache)
        for field in reversed(fields):
            reverse = field.startswith("-")
            field_name = field[1:] if reverse else field
            rslt.sort(key=lambda obj: self._get_field_value(obj, field_name), reverse=reverse)

        cloned_query = self.query.clone()
        if hasattr(cloned_query, "order_by"):
            cloned_query.order_by = list(fields)

        return self.__class__(
            self.model,
            rslt,
            cloned_query,
            using=self._db,
            hints=self._hints,
        )

    def __iter__(self):
        rslt = self._result_cache
        if hasattr(self.query, "order_by") and self.query.order_by:
            ordering = self.query.order_by
            if ordering:
                rslt = list(rslt)
                for field in reversed(ordering):
                    reverse = field.startswith("-")
                    field_name = field[1:] if reverse else field
                    rslt.sort(
                        key=lambda obj: self._get_field_value(obj, field_name), reverse=reverse
                    )
        return iter(rslt)
