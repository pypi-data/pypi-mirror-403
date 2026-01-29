from .PageProperties import PageProperties as _PageProperties

class _Parser:

    def __init__(self) -> None:
        self.page_props = _PageProperties.parse

Parser = _Parser()
__all__ = ["Parser"]
