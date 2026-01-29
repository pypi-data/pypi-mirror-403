from typing import TypeVar, Generic, TYPE_CHECKING

if TYPE_CHECKING:
    from ...schemas.orm.database.DatabasesContainer import DatabasesContainer as _DatabasesContainer

TContainer = TypeVar('TContainer', bound = '_DatabasesContainer')

class DatabasesRepo(Generic[TContainer]):

    def __init__(self):
        self.container: TContainer
    
    @staticmethod
    def generic(database_id : str):
        from .databases import DatabaseClient
        return DatabaseClient.generic(database_id)

class _Repositories(Generic[TContainer]):

    def __init__(self):
        from .pages import _Pages
        self.pages = _Pages()
        self.databases: DatabasesRepo[TContainer] = DatabasesRepo()

repo: _Repositories = _Repositories()
__all__ = ["repo", "_Repositories"]