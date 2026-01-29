from typing import Optional

class ORMConfig:

    "Configuração global do ORM"
    
    _timezone: str = "Etc/UTC"
    _configured: bool = False
    
    @classmethod
    def configure(cls,
        timezone : str = "Etc/UTC"
    ):

        "Configura o ORM"

        cls._timezone = timezone
        cls._configured = True
    
    @classmethod
    def get_timezone(cls) -> str:

        "Retorna a timezone configurada"
        
        return cls._timezone

__all__ = ["ORMConfig"]