from typing   import Dict, Any, Optional, Callable, ClassVar, TypeVar, Type
from pydantic import field_validator
from ...schemas.dto import BaseModelSdk

T = TypeVar('T', bound='NotionDatabase')

class NotionConfigMeta:

    "Metadados de configuração da database do Notion"
    
    def __init__(self, config_class):

        self.database_id : Optional[str]       = getattr(config_class, 'database_id', None)
        self.mappings    : Dict[str, Any]      = getattr(config_class, 'mappings', {})
        self.validators  : Dict[str, Callable] = getattr(config_class, 'validators', {})
        self.computed    : Dict[str, Callable] = getattr(config_class, 'computed', {})
        
        transformers_config: Dict[str, Callable] = getattr(config_class, 'transformers', {})

        # Processa mappings para separar nome e transformer
        self.field_mappings : Dict[str, str]      = {}
        self.transformers   : Dict[str, Callable] = {}
        
        for field_name, mapping in self.mappings.items():

            if isinstance(mapping, str):

                # Mapping simples: "field": "Notion Name"
                self.field_mappings[field_name] = mapping

            elif isinstance(mapping, tuple) and len(mapping) == 2:

                # Mapping com transformer: "field": ("Notion Name", lambda x: ...)
                self.field_mappings[field_name] = mapping[0]
                self.transformers[field_name]   = mapping[1]

            else:

                raise ValueError(
                    f"Mapping inválido para '{field_name}'. "
                    f"Use: 'Notion Name' ou ('Notion Name', transformer_func)"
                )
        
        self.transformers.update(transformers_config)

class NotionDatabaseMeta(type(BaseModelSdk)):

    "Metaclass que processa a classe e injeta funcionalidades do Notion"
    
    _notion_config: NotionConfigMeta
    
    def __new__(mcs, name, bases, namespace, **kwargs):

        # Cria a classe Pydantic
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        
        # Se tem NotionConfig, processa
        if hasattr(cls, 'NotionConfig'):

            config = NotionConfigMeta(cls.NotionConfig)
            
            # Injeta o config processado
            cls._notion_config = config  # type: ignore
            
            if not config.database_id:
                raise AttributeError("Database ID is missing")
            
            # Injeta validators customizados do NotionConfig
            if config.validators:

                for field_name, validator_func in config.validators.items():
                    
                    # Cria um validator Pydantic dinâmico
                    validator_name = f'validate_{field_name}_notion'
                    
                    def make_validator(func):
                        def validator(cls, v):
                            return func(v)
                        return field_validator(field_name)(validator)
                    
                    setattr(cls, validator_name, make_validator(validator_func))
        
        return cls

class NotionDatabase(BaseModelSdk, metaclass = NotionDatabaseMeta):

    """
    Classe base para schemas de databases do Notion.
    
    Uso:
    ----
    class AccountsDB(NotionDatabase):
        name: str
        credit: float
        type: List[str]
        
        class NotionConfig:
            mappings = {
                "name": "Name",
                "credit": "Credit",
                "type": ("Type", lambda x: [s["name"] for s in x] if x else [])
            }
    """

    _notion_config: ClassVar[NotionConfigMeta]
    
    @classmethod
    def from_notion_page(
        cls : Type[T],
        page_properties : Dict[str, Any],
        page_parser     : Optional[Callable] = None
    ) -> Optional[T]:
        
        """
        Cria uma instância do schema a partir de propriedades parseadas do Notion.
        
        Args:
            page_properties: Dict com propriedades já parseadas pelo PropertyExtractor
            page_parser: Função de parsing (se as propriedades ainda não foram parseadas)
        
        Returns:
            Instância do schema ou None se parsing falhar
        """
        
        if not hasattr(cls, '_notion_config'):
            raise AttributeError(
                f"{cls.__name__} não tem NotionConfig definido. "
                f"Adicione uma subclasse NotionConfig com os mappings."
            )
        
        config: NotionConfigMeta = cls._notion_config
        
        # Se recebeu a página raw, faz o parsing
        if page_parser and 'properties' in page_properties:
            page_properties = page_parser(page_properties)
        
        if not page_properties:
            return None
        
        result = {}
        
        # Processa campos mapeados
        for field_name, notion_name in config.field_mappings.items():

            raw_value = page_properties.get(notion_name)
            
            # Aplica transformer se existir
            if field_name in config.transformers:
                value = config.transformers[field_name](raw_value)
            else:
                value = raw_value
            
            result[field_name] = value
        
        # Cria instância temporária para computed fields
        instance = cls(**result)
        
        # Processa computed fields
        for field_name, compute_func in config.computed.items():

            computed_value     = compute_func(instance)
            result[field_name] = computed_value
        
        # Retorna instância final com computed fields
        return cls(**result)
    
    @classmethod
    def id(cls) -> str:

        "Retorna o nome da database no Notion"

        if hasattr(cls, '_notion_config'):
            return cls._notion_config.database_id or cls.__name__
        
        return cls.__name__
    
    @classmethod
    def field_name(cls,
        python_field : str
    ) -> Optional[str]:

        "Retorna o nome do campo no Notion a partir do nome Python"

        if hasattr(cls, '_notion_config'):
            return cls._notion_config.field_mappings.get(python_field)
        
        return None
    
    @classmethod
    def mappings(cls) -> Dict[str, str]:

        "Retorna todos os mappings field_python -> field_notion"

        if hasattr(cls, '_notion_config'):
            return cls._notion_config.field_mappings.copy()
        
        return {}

__all__ = ["NotionDatabase"]