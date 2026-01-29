from .QueryFilter import QueryFilter as _QueryFilter
from .QuerySort   import QuerySort   as _QuerySort
from .SetProperty import SetProperty as _SetProperty

class _Common:

    def __init__(self) -> None:
        self.QueryFilter = _QueryFilter
        self.QuerySort   = _QuerySort
        self.SetProperty = _SetProperty

Common = _Common()
__all__ = ["Common"]