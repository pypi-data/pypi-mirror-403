from __future__ import annotations

from .error import (
    InterfaceAlreadyRegisteredError,
    InterfaceNotFoundError,
)
from .factory import ClassInterfaceFactory

# Singleton instance of InterfaceFactory
InterfaceFactory = ClassInterfaceFactory()


__all__ = [
    "InterfaceNotFoundError",
    "InterfaceAlreadyRegisteredError",
    "InterfaceFactory",
]
