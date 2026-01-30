from typing import Any, Iterable

from django.db.models.query import QuerySet
from django.db.models.sql import Query

from .data import DataMixin
from .filter import FilterMixin
from .order import OrderMixin


class VirtualQuerySet(DataMixin, FilterMixin, OrderMixin, QuerySet):
    def __init__(
        self, model=None, data: Iterable[Any] | None = None, query=None, using=None, hints=None
    ):
        if query is None and model is not None:
            query = Query(model)
        super().__init__(model=model, query=query, using=using, hints=hints)
        self._result_cache = self._from_data(data or [])
        self._prefetch_done = True

    def _clone(self):
        return self.__class__(
            self.model,
            list(self._result_cache),
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def __getitem__(self, k):
        if isinstance(k, slice):
            return self.__class__(
                self.model,
                self._result_cache[k],
                self.query.clone(),
                using=self._db,
                hints=self._hints,
            )
        return self._result_cache[k]

    def all(self):
        return self._clone()

    def count(self):
        return len(self._result_cache)

    def exists(self):
        return len(self._result_cache) > 0

    def first(self):
        return self._result_cache[0] if self._result_cache else None

    def last(self):
        return self._result_cache[-1] if self._result_cache else None

    def values(self, *fields):
        """Return a list of dictionaries with the specified fields."""
        if not fields:
            # If no fields specified, return all attributes as dict
            return [
                {key: getattr(obj, key) for key in dir(obj) if not key.startswith('_')}
                for obj in self._result_cache
            ]
        return [{field: getattr(obj, field, None) for field in fields} for obj in self._result_cache]

    def values_list(self, *fields, flat=False):
        """Return a list of tuples with the specified fields."""
        if flat:
            if len(fields) != 1:
                raise TypeError("'flat' is not valid when values_list is called with more than one field.")
            return [getattr(obj, fields[0], None) for obj in self._result_cache]
        if not fields:
            return [tuple(getattr(obj, key, None) for key in dir(obj) if not key.startswith('_')) for obj in self._result_cache]
        return [tuple(getattr(obj, field, None) for field in fields) for obj in self._result_cache]

    def none(self):
        """Return an empty QuerySet."""
        return self.__class__(
            self.model,
            [],
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def __len__(self):
        return len(self._result_cache)
