from typing   import Optional, Generic, TypeVar
from pydantic import validate_call
from ....client            import get_client as _get_client
from ....schemas.responses import Schemas    as _schm
from ...mapping.database   import NotionDatabase as _NotionDatabase
from ...mapping            import Mapping        as _map
from ...common.QueryFilter import QueryFilter    as _Filter, _NotionFilter
from ...common.QuerySort   import QuerySort      as _Sort, _NotionSort
from ...parsers            import Parser         as _parser

TDB = TypeVar('TDB', bound = _NotionDatabase)

class SearchPage(Generic[TDB]):

    def __init__(self,
        database_id : str,
        generic_response : bool = False
    ) -> None:
        self._database_id = database_id
        self._generic_response = generic_response
        self.query_limit : int = 100
        self.filter = _Filter
        self._filter_obj : Optional[_NotionFilter] = None
        self.sort = _Sort
        self._sort_obj : Optional[_NotionSort] = None
    
    def set_limit(self,
        page_limit : int
    ):
        "Define o limite de páginas a serem retornadas na requisição"
        self.query_limit = page_limit
        return self

    def set_sort(self,
        sort_obj : _NotionSort
    ):
        "Define a classificação a ser usada na query"
        self._sort_obj = sort_obj
        return self

    def set_filter(self,
        filter_obj : _NotionFilter
    ):
        "Define o filtro a ser usado na query"
        self._filter_obj = filter_obj
        return self

    @validate_call
    async def call(self,
        map_properties : bool = True,
        raw_response   : bool = False
    ) -> _schm.databases.Query[TDB]:

        payload = {}
        if self.query_limit:
            payload["page_size"] = self.query_limit
        if self._sort_obj:
            payload["sorts"] = self._sort_obj.to_dict()
        if self._filter_obj:
            payload["filter"] = self._filter_obj.to_dict()

        client = _get_client()

        query = await client.databases.query(
            database_id = self._database_id,
            json_data   = payload
        )

        if query['object'] == 'error':
            error = _schm.errors.Error(**query)
            raise KeyError(error.__dict__)

        pages = []
        results = query["results"]

        if not raw_response:
            
            if map_properties:

                parser = None
                if not self._generic_response:
                    # Tenta pegar parser do registry
                    parser = _map.registry.get_parser(
                        database_id = self._database_id, 
                        page_parser = _parser.page_props
                    )
                
                # Fallback: se database não registrada, usa parser genérico
                if not parser:
                    parser = _parser.page_props
                
                for page in results:
                    page_properties = parser(page)
                    page["properties"] = page_properties if page_properties else None
                    pages.append(page)

        results = pages

        return _schm.databases.Query(**query)

__all__ = ["SearchPage"]