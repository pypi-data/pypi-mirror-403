"""Storage backend module"""

from fabric.storage.base import BaseStorage
from fabric.storage.memory import MemoryStorage

__all__ = [
    "BaseStorage",
    "MemoryStorage",
]
