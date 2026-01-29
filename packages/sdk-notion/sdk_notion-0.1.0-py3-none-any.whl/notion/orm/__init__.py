from .config       import ORMConfig as _config
from .common       import Common    as _common
from .parsers      import Parser    as _parser
from .mapping      import Mapping   as _mapping
from .repositories import repo      as _repositories

class _NotionOrm:

    def __init__(self) -> None:
        self.config  = _config
        self.common  = _common
        self.parser  = _parser
        self.mapping = _mapping
        self.repo    = _repositories

NotionOrm = _NotionOrm()
__all__ = ["NotionOrm"]