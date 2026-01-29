from typing   import Optional, Literal, Generic, TypeVar
from pydantic import validate_call
from ....schemas.responses import Schemas as _schm
from ...mapping.database   import NotionDatabase as _NotionDatabase
from ...mapping            import Mapping        as _map
from ...parsers            import Parser         as _parser
from ...common.SetProperty import SetProperty    as _setProperty
from ..pages.CreatePage import CreatePage  as _CreatePage

TDB = TypeVar('TDB', bound = _NotionDatabase)

class CreateDatabasePage(Generic[TDB]):
    
    def __init__(self,
        database_id  : str,
        generic_response : bool = False 
    ) -> None:
        self._database_id  = database_id
        self._generic_response = generic_response
        self._instance     = _CreatePage().set_parent(
            type      = "database_id",
            parent_id = self._database_id
        )
        self.set_property = _setProperty(self, self._instance.data["properties"])

    @validate_call
    def set_template(self,
        type        : Literal["default", "template_id"],
        template_id : Optional[str] = None
    ):
        self._instance.set_template(
            type = type,
            template_id = template_id
        )
        return self

    @validate_call
    def set_title(self,
        prop_name  : Optional[str],
        prop_value : Optional[str]
    ):
        self._instance.set_title(
            prop_name = prop_name,
            prop_value = prop_value
        )
        return self

    @validate_call
    def set_icon(self,
        type    : Literal["external"],
        content : Optional[str] = None
    ):
        self._instance.set_icon(
            type = type,
            content = content
        )
        return self

    @validate_call
    async def call(self,
        map_properties : bool = True,
        raw_response   : bool = False
    ) -> _schm.pages.Page[TDB]:

        page = await self._instance.call(
            parse_properties = False
        )

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
                
                page = page.model_dump()
                mapped_properties = parser(page = page)
                page["properties"] = mapped_properties

                page = _schm.pages.Page(**page)

        return page

__all__ = ["CreateDatabasePage"]