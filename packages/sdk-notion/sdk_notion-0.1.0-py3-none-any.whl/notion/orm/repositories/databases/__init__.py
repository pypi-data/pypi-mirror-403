from typing import Generic, TypeVar
from ...mapping.database import NotionDatabase as _NotionDatabase
from ..pages import _Pages as _Pages
from .CreateDatabasePage import CreateDatabasePage as _CreateDatabasePage
from .SearchPage         import SearchPage         as _SearchPage
from .SearchPageProperty import SearchPageProperty as _SearchPageProperty

TDB = TypeVar('TDB', bound = _NotionDatabase)

class DatabaseClient(Generic[TDB]):
    
    def __init__(self,
        database_id : str,
        generic_response : bool = False
    ) -> None:

        self._database_id = database_id
        self._generic_response = generic_response

    @property
    def CreateDatabasePage(self) -> _CreateDatabasePage[TDB]:
        return _CreateDatabasePage(
            database_id = self._database_id,
            generic_response = self._generic_response
        )

    @property
    def SearchPage(self) -> _SearchPage[TDB]:
        return _SearchPage(
            database_id = self._database_id,
            generic_response = self._generic_response
        )

    @property
    def SearchPageProperty(self) -> _SearchPageProperty:
        return _SearchPageProperty(
            database_id = self._database_id
        )

    @property
    def page(self) -> _Pages[TDB]:
        return _Pages(
            database_id = self._database_id,
            generic_response = self._generic_response
        )

    @staticmethod
    def generic(database_id : str) -> 'DatabaseClient[_NotionDatabase]':
        
        "Acessa database sem schema definido"
        
        return DatabaseClient(
            database_id = database_id,
            generic_response = True
        )

__all__ = ["DatabaseClient"]