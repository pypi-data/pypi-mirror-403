from typing import Optional, Generic, TypeVar
from ...mapping.database import NotionDatabase as _NotionDatabase
from .CreatePage      import CreatePage      as _CreatePage
from .GetPage         import GetPage         as _GetPage
from .GetPageProperty import GetPageProperty as _GetPageProperty

TDB = TypeVar('TDB', bound = _NotionDatabase)

class _Pages(Generic[TDB]):

    def __init__(self,
        database_id : Optional[str] = None,
        generic_response : bool = False
    ) -> None:

        self._database_id  = database_id
        self._generic_response = generic_response
        
        self.CreatePage      = _CreatePage
        self.GetPageProperty = _GetPageProperty

    @property
    def GetPage(self) -> _GetPage:
        return _GetPage(
            database_id = self._database_id,
            generic_response = self._generic_response
        )

Pages = _Pages()
__all__ = ["Pages", "_Pages"]