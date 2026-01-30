"""Django VirtualQuerySet - QuerySet-like objects not backed by a database."""

__version__ = "0.1.1"

from .managers import VirtualManager
from .queryset import VirtualQuerySet

default_app_config = "virtualqueryset.apps.VirtualQuerySetConfig"  # noqa: E402

__all__ = [
    "VirtualQuerySet",
    "VirtualManager",
]
