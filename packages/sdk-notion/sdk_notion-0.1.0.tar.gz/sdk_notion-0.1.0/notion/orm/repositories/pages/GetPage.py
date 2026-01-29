from typing import Dict, Any, Optional, TypeVar, Generic
from ....schemas.responses.pages.Page   import Page        as _schmPage
from ....schemas.responses.errors.Error import Error       as _schmError
from ....client                         import get_client  as _get_client
from ...mapping.database import NotionDatabase as _NotionDatabase
from ...mapping          import Mapping        as _map
from ...parsers          import Parser         as _parser

TDB = TypeVar('TDB', bound =_NotionDatabase)

class GetPage(Generic[TDB]):

    def __init__(self,
        database_id  : Optional[str] = None,
        generic_response : bool = False
    ) -> None:
        self._database_id : Optional[str] = database_id
        self._generic_response = generic_response
        self._pageid : str

    def set_pageid(self,
        id : str
    ) -> 'GetPage[TDB]':
        self._pageid = id
        return self

    def set_database(self,
        id : str
    ) -> 'GetPage[TDB]':
        self._database_id = id
        return self

    async def select(self,
        property : str
    ) -> Optional[Any]:
        
        client = _get_client()

        page : Dict[str, Any] = await client.pages.get(
            page_id = self._pageid
        )

        if page['object'] == 'error':
            error = _schmError(**page)
            raise KeyError(error.__dict__)

        page["properties"] = _parser.page_props(page = page)
        if page["properties"] is None:
            return None
        allprops = page["properties"]

        return allprops[property]

    async def call(self,
        map_properties : bool = True,
        raw_response   : bool = False
    ) -> _schmPage[TDB]:

        client = _get_client()

        page : Dict[str, Any] = await client.pages.get(
            page_id = self._pageid
        )

        if page['object'] == 'error':
            error = _schmError(**page)
            raise KeyError(error.__dict__)

        if not raw_response:

            if map_properties and self._database_id:

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
                
                mapped_properties = parser(page = page)
                page["properties"] = mapped_properties

            elif map_properties:

                page["properties"] = _parser.page_props(page = page)

        return _schmPage(**page)
