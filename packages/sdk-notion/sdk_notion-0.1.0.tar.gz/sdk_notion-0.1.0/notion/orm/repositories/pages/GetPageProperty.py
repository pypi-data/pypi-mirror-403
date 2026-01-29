from pydantic import validate_call
from typing   import Dict, Any, Optional
from ....schemas.responses.errors.Error import Error       as _schmError
from ....client                         import get_client  as _get_client
from ...parsers.PageProperties import PageProperties as _PageProperties

class GetPageProperty:

    """
    # CUIDADO AO UTILIZAR!!
    ### [Bug Conhecido](https://community.latenode.com/t/notion-api-relation-property-showing-empty-array-despite-ui-showing-connected-pages/25780) na API do Notion impede retornos confiáveis em propriedades paginadas
    Ultimo teste : 2026-01-10
    """

    def __init__(self) -> None:
        self._pageid   : str
        self._propname : str

    @validate_call
    def set_pageid(self,
        id : str
    ):
        self._pageid = id
        return self

    @validate_call
    def set_propname(self,
        name : str
    ):
        self._propname = name
        return self

    async def call(self,
        raw_response : bool = False
    ) -> Optional[Dict[str, Any]]:

        client = _get_client()

        getprop = await client.pages.get_property(
            page_id       = self._pageid,
            property_name = self._propname
        )

        if getprop['object'] == 'error':
            error = _schmError(**getprop)
            raise KeyError(error.__dict__)

        prop_data = getprop.get("results")
        if getprop.get("object") == "property_item":
            prop_data = [getprop]
        if not prop_data:
            return None

        if not raw_response:

            result = _PageProperties.parse(
                page = prop_data[0]
            )
        
        else:

            result = prop_data[0]

        return result
    