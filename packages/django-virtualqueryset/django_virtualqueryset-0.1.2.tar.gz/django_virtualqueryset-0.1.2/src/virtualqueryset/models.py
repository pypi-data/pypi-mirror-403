"""Base models for virtual models."""

from django.db import models


class VirtualModel(models.Model):
    """Base class for virtual models (no database table)."""

    class Meta:
        abstract = True
        managed = False

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a virtual model and cannot be saved to database. "
            "Override save() if you want to implement custom persistence."
        )

    def delete(self, *args, **kwargs):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a virtual model and cannot be deleted from database. "
            "Override delete() if you want to implement custom deletion."
        )
