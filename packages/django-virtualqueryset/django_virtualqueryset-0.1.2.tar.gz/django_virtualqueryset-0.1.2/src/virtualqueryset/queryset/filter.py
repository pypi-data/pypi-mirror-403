from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q


class FilterMixin:
    def _evaluate_q_object(self, q_obj, obj):
        """Evaluate a Q object against an object."""
        if not q_obj.children:
            return True

        results = []
        for child in q_obj.children:
            if isinstance(child, Q):
                child_result = self._evaluate_q_object(child, obj)
            else:
                lookup, value = child
                child_result = self._evaluate_lookup(obj, lookup, value)

            if q_obj.negated:
                child_result = not child_result
            results.append(child_result)

        if q_obj.connector == "AND":
            return all(results)
        else:  # OR
            return any(results)

    def _evaluate_lookup(self, obj, lookup, value):
        """Evaluate a single lookup against an object."""

        def _value(obj, attr):
            return getattr(obj, attr, "")

        def _get_field_value_getter(field_name):
            def field_value_getter(obj):
                return _value(obj, field_name)

            return field_value_getter

        if "__" in lookup:
            field_name, lookup_type = lookup.rsplit("__", 1)
            field_value_getter = _get_field_value_getter(field_name)

            method_name = f"get_look_type_{lookup_type}"
            if hasattr(self, method_name):
                return len(getattr(self, method_name)([obj], field_value_getter, value)) > 0
            return False
        else:
            return getattr(obj, lookup, None) == value

    def get_look_type_icontains(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if value.lower() in str(field_value_getter(obj)).lower()]

    def get_look_type_contains(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if value in str(field_value_getter(obj))]

    def get_look_type_exact(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if field_value_getter(obj) == value]

    def get_look_type_in(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if field_value_getter(obj) in value]

    def get_look_type_gt(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if field_value_getter(obj) > value]

    def get_look_type_gte(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if field_value_getter(obj) >= value]

    def get_look_type_lt(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if field_value_getter(obj) < value]

    def get_look_type_lte(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if field_value_getter(obj) <= value]

    def get_look_type_isnull(self, rslt, field_value_getter, value):
        if value:
            return [obj for obj in rslt if field_value_getter(obj) in (None, "")]
        else:
            return [obj for obj in rslt if field_value_getter(obj) not in (None, "")]

    def get_look_type_startswith(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if str(field_value_getter(obj)).startswith(value)]

    def get_look_type_istartswith(self, rslt, field_value_getter, value):
        return [
            obj for obj in rslt if str(field_value_getter(obj)).lower().startswith(value.lower())
        ]

    def get_look_type_endswith(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if str(field_value_getter(obj)).endswith(value)]

    def get_look_type_iendswith(self, rslt, field_value_getter, value):
        return [obj for obj in rslt if str(field_value_getter(obj)).lower().endswith(value.lower())]

    def filter(self, *args, **kwargs):
        rslt = self._result_cache

        def _value(obj, attr):
            return getattr(obj, attr, "")

        def _get_field_value_getter(field_name):
            def field_value_getter(obj):
                return _value(obj, field_name)

            return field_value_getter

        # Handle Q objects in *args
        for q_obj in args:
            if isinstance(q_obj, Q):
                rslt = [obj for obj in rslt if self._evaluate_q_object(q_obj, obj)]
            else:
                # If it's not a Q object, treat it as kwargs
                if hasattr(q_obj, "items"):
                    for lookup, value in q_obj.items():
                        if "__" in lookup:
                            field_name, lookup_type = lookup.rsplit("__", 1)
                            field_value_getter = _get_field_value_getter(field_name)
                            method_name = f"get_look_type_{lookup_type}"
                            if hasattr(self, method_name):
                                rslt = getattr(self, method_name)(rslt, field_value_getter, value)
                        else:
                            rslt = [obj for obj in rslt if getattr(obj, lookup, None) == value]

        # Handle kwargs
        for lookup, value in kwargs.items():
            if "__" in lookup:
                field_name, lookup_type = lookup.rsplit("__", 1)
                field_value_getter = _get_field_value_getter(field_name)

                method_name = f"get_look_type_{lookup_type}"
                if hasattr(self, method_name):
                    rslt = getattr(self, method_name)(rslt, field_value_getter, value)
            else:
                rslt = [obj for obj in rslt if getattr(obj, lookup, None) == value]

        return self.__class__(
            self.model,
            rslt,
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def exclude(self, *args, **kwargs):
        filtered = self.filter(*args, **kwargs)
        excluded_ids = {id(obj) for obj in filtered._result_cache}
        rslt = [obj for obj in self._result_cache if id(obj) not in excluded_ids]
        return self.__class__(
            self.model,
            rslt,
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def get(self, **kwargs):
        rslt = self._result_cache
        for attr, value in kwargs.items():
            rslt = [obj for obj in rslt if getattr(obj, attr) == value]

        if len(rslt) == 1:
            return rslt[0]

        if not rslt:
            model_name = self.model.__name__ if self.model else "Object"
            raise ObjectDoesNotExist(f"{model_name} matching query does not exist.")

        model_name = self.model.__name__ if self.model else "Object"
        raise MultipleObjectsReturned(
            f"get() returned more than one {model_name} -- it returned {len(rslt)}!"
        )
