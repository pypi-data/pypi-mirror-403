from typing import Optional, Literal, List
from ....client               import get_client  as _get_client
from ....schemas.orm.database import Schemas     as _schm
from ....schemas.responses    import Schemas     as _schmResponses
from ...common.QueryFilter import QueryFilter as _Filter, _NotionFilter
from ...parsers            import Parser      as _parser

class SearchPageProperty:

    """
    # CUIDADO AO UTILIZAR!!
    ### [Bug Conhecido](https://community.latenode.com/t/notion-api-relation-property-showing-empty-array-despite-ui-showing-connected-pages/25780) na API do Notion impede retornos confiáveis em propriedades paginadas
    Ultimo teste : 2026-01-10
    """

    def __init__(self, database_id : str) -> None:
        self._database_id = database_id
        self.filter = _Filter
        self._filter_obj : Optional[_NotionFilter] = None
        self._property_type = None
    
    def set_filter(self,
        property_type : Literal[
            "unique_id",
            "icon",
            "title",
            "number",
            "checkbox",
            "start_date",
            "end_date",
            #"relation",
            "text",
            "rich_text",
            "select",
            "multi_select",
            "status",
            "media",
            "url",
            "email",
            "phone",
            "person",
            "place"
        ],
        filter_obj : _NotionFilter
    ):
        "Define o filtro a ser usado na query"
        self._property_type = property_type
        self._filter_obj = filter_obj
        return self

    async def call(self,
        raw_response : bool = False
    ) -> List[_schm.SearchPageProperty]:

        if not self._property_type:
            raise TypeError("Filter is not fully defined")

        payload = {}
        if self._filter_obj:
            payload["filter"] = self._filter_obj.to_dict()

        client = _get_client()

        query = await client.databases.query_propriety(
            database_id    = self._database_id,
            propriety_type = self._property_type,
            json_data      = payload
        )

        if query['object'] == 'error':
            error = _schmResponses.errors.Error(**query)
            raise KeyError(error.__dict__)
        
        results = query["results"]

        pages = []
        for page in results:
            if raw_response:
                page["properties"] = _parser.page_props(page = page)
            pages.append(page)
            
        result = []
        for page in pages:
            prop_value = page["properties"]
            if prop_value:
                prop_value = list(prop_value.values())[0]
            result.append(
                _schm.SearchPageProperty(
                    page_id    = page["id"],
                    prop_value = prop_value 
                )
            )

        return result
