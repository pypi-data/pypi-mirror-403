import httpx
from typing import Dict

class Databases:

    def __init__(self, headers : Dict[str, str]):
        self._headers = {**headers, "Notion-Version": "2022-06-28"}

    async def get(self, database_id):

        "Buscar informações de um Banco de Dados"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.get(
                f'https://api.notion.com/v1/databases/{database_id}',
                headers = self._headers
            )

            return response.json()

    async def query(self, database_id, json_data = {}):

        "Buscar as Páginas de um Banco de Dados"
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.post(
                f'https://api.notion.com/v1/databases/{database_id}/query',
                headers = self._headers,
                json    = json_data
            )

            return response.json()

    async def query_propriety(self, database_id, propriety_type, json_data = {}):

        "Buscar as Páginas de um Banco de Dados filtrando por uma Propriedade"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.post(
                f'https://api.notion.com/v1/databases/{database_id}/query?filter_properties={propriety_type}',
                headers = self._headers,
                json    = json_data
            )
            
            return response.json()

    async def update(self, database_id, json_data):

        "Atualiza as informações sobre um Banco de Dados"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.patch(
                f'https://api.notion.com/v1/databases/{database_id}',
                headers = self._headers,
                json    = json_data
            )
            
            return response.json()

__all__ = ["Databases"]