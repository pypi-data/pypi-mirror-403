import httpx
from typing import Dict, Any

class Pages:

    def __init__(self, headers : Dict[str, str]):
        self._headers = headers

    async def get(self,
        page_id : str
    ):

        "Buscar informações de uma Página"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.get(
                f'https://api.notion.com/v1/pages/{page_id}',
                headers = self._headers
            )

            return response.json()

    async def get_property(self,
        page_id : str,
        property_name : str
    ):

        "Buscar por informações de uma Propriedade em uma Página"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.get(
                f'https://api.notion.com/v1/pages/{page_id}/properties/{property_name}',
                headers = self._headers
            )

            return response.json()

    async def update_properties(self,
        page_id : str,
        json_data : Dict[str, Any]
    ):

        "Atualiza as Propriedades de uma Página"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response =  await client.patch(
                f'https://api.notion.com/v1/pages/{page_id}',
                headers = self._headers,
                json=json_data
            )

            return response.json()

    async def create(self,
        json_data : Dict[str, Any]
    ):

        "Criar uma nova Página"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.post(
                f'https://api.notion.com/v1/pages',
                headers = self._headers,
                json    = json_data
            )

            return response.json()

__all__ = ["Pages"]