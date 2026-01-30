from django.db import models
from typing import Any, List
from .queryset import VirtualQuerySet


class VirtualManager(models.Manager):
    queryset_class = VirtualQuerySet

    def get_queryset(self):
        data = self.get_data()
        return self.queryset_class(model=self.model, data=data)

    def get_data(self) -> List[Any]:
        return []


__all__ = ["VirtualManager"]
