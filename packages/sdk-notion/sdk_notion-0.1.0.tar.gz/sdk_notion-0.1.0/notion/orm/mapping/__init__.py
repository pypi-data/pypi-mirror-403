from .database import NotionDatabase   as _NotionDatabase
from .registry import DatabaseRegistry as _DatabaseRegistry

class _Mapping:

    NotionDatabase = _NotionDatabase

    def __init__(self) -> None:
        self.registry = _DatabaseRegistry

Mapping = _Mapping()
__all__ = ["Mapping"]