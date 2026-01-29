from typing import Dict, Optional
from .blocks    import Blocks
from .pages     import Pages
from .databases import Databases

class Client:

    "Client singleton da API Notion"
    
    _headers  : Optional[Dict[str, str]] = None
    _instance : Optional['Client']       = None
    
    def __init__(self):
        self._blocks    = None
        self._pages     = None
        self._databases = None
    
    @classmethod
    def configure(cls, headers : Dict[str, str]):
        
        "Configura o client com headers"
        
        cls._headers = headers
    
    @classmethod
    def get_instance(cls) -> 'Client':

        "Retorna a instância configurada"

        if cls._instance is None:
            
            cls._instance = Client()
        
        return cls._instance
    
    @property
    def blocks(self) -> Blocks:
        
        if self._blocks is None:
        
            if Client._headers is None:
                raise RuntimeError("Client não configurado. Instancie NotionIntegration primeiro.")
        
            self._blocks = Blocks(Client._headers)
        
        return self._blocks
    
    @property
    def pages(self) -> Pages:
        
        if self._pages is None:
        
            if Client._headers is None:
                raise RuntimeError("Client não configurado. Instancie NotionIntegration primeiro.")
        
            self._pages = Pages(Client._headers)
        
        return self._pages
    
    @property
    def databases(self) -> Databases:

        if self._databases is None:

            if Client._headers is None:
                raise RuntimeError("Client não configurado. Instancie NotionIntegration primeiro.")
            
            self._databases = Databases(Client._headers)
        
        return self._databases

def get_client() -> Client:
    return Client.get_instance()

__all__ = ["Client", "get_client"]