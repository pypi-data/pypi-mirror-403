from .PageProperty import PageProperty as _PageProperty

class _Acessors:

    def __init__(self) -> None:
        self.PageProperty = _PageProperty

Acessors = _Acessors
__all__ = ["Acessors"]