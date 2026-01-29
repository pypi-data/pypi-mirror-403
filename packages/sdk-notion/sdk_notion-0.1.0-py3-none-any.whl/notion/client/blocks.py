import httpx
from typing import Dict

class Blocks:

    "Reference: https://developers.notion.com/reference/retrieve-a-block"

    def __init__(self, headers : Dict[str, str]):
        self._headers = headers

    async def get_children(self, page_id : str):

        "Busca pelos blocos de uma página"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:

            response = await client.get(
                f'https://api.notion.com/v1/blocks/{page_id}/children',
                headers = self._headers
            )

            return response.json()

__all__ = ["Blocks"]