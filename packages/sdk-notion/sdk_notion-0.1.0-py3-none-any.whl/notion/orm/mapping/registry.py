from typing    import Dict, Any, Optional, Callable, Type
from .database import NotionDatabase as _NotionDatabase

class DatabaseRegistry:

    """
    Registry global de databases do Notion.
    Permite acessar schemas e criar parsers dinamicamente.
    """
    
    _databases: Dict[str, Type[_NotionDatabase]] = {}
    
    @classmethod
    def register(cls,
        database_class : Type[_NotionDatabase]
    ) -> None:

        "Registra uma database no registry"

        db_name = database_class.id()
        cls._databases[db_name] = database_class

    @classmethod
    def auto_register(cls,
        *database_classes : Type[_NotionDatabase]
    ) -> None:
        
        "Registra múltiplas databases de uma vez"
        
        for db_class in database_classes:
            cls.register(db_class)

    @classmethod
    def get(cls,
        database_id : str
    ) -> Optional[Type[_NotionDatabase]]:

        "Retorna a classe de schema de uma database"

        return cls._databases.get(database_id)
    
    @classmethod
    def get_parser(cls,
        database_id : str,
        page_parser : Callable
    ) -> Callable:

        """
        Retorna uma função parser para a database.
        
        Args:
            database_id: ID da Database
            page_parser: Função que parseia páginas (ex: PageProperties.parse)
        
        Returns:
            Função parser ou None se database não encontrada
        """

        db_class = cls.get(database_id)
        if not db_class:
            raise ValueError(f"Database de ID '{database_id}' não está registrada")
        
        def parser(page : Dict[str, Any]) -> Optional[_NotionDatabase]:
            return db_class.from_notion_page(page, page_parser)
        
        return parser
    
    @classmethod
    def list_databases(cls) -> list[str]:

        "Lista todas as databases registradas"

        return list(cls._databases.keys())
    
    @classmethod
    def generate_literal_type(cls) -> str:
        
        "Gera o código do Literal com todas as databases registradas"
        
        db_names = list(cls._databases.keys())
        literal_str = ", ".join([f'"{name}"' for name in db_names])
        
        return f"Literal[{literal_str}]"

    @classmethod
    def get_database_class_by_id(cls,
        db_id : str
    ) -> Optional[Type[_NotionDatabase]]:
        
        "Retorna a classe schema baseado no nome da database"

        return cls._databases.get(db_id)
