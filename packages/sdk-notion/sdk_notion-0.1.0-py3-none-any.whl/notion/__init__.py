from typing import Type, TypeVar, Generic, Union, Literal
from .auth import headers as _headers
from .schemas.orm.database.DatabasesContainer import DatabasesContainer as _DatabasesContainer
from .orm.repositories import _Repositories
from .orm.config       import ORMConfig
from .client           import Client as _Client

TContainer = TypeVar('TContainer', bound = _DatabasesContainer)

class Notion(Generic[TContainer]):

    "Classe principal para configurar a integração Notion."
    
    orm: '_ORM[TContainer]'
    
    def __init__(self,
        api_token     : str,
        api_version   : Union[Literal["legacy", "data_sources"], str] = "data_sources",
        orm_container : Type[TContainer] = _DatabasesContainer,
        timezone      : str = "Etc/UTC"
    ): 
        
        """
            ### Integration Params
            - **api_token** = Bearer Token de Integração com a API Notion.
            - **api_version** = Seleção entre versão `legacy` com Databases e versão mais nova com `data_sources`, permitindo inserir versão personalizada. Valor padrão: `legacy` *(2022-06-28)*.
            - **orm_container** = Databases Container com configuração de ORM personalizada com classe base de tipo `types.DatabasesContainer`
        """

        headers = _headers(
            api_token   = api_token,
            api_version = api_version
        )
        _Client.configure(headers)
        self.client = _Client.get_instance()

        ORMConfig.configure(timezone = timezone)
        self.orm = _ORM(databases_container = orm_container)

        self.DatabasesContainer = _DatabasesContainer

class _ORM(Generic[TContainer]):

    "Namespace ORM com tipo propagado"
    
    repo: _Repositories[TContainer]
    
    def __init__(self,
        databases_container : Type[TContainer]
    ):
        self.repo = _Repositories()
        self.repo.databases.container = databases_container()

__all__ = ["Notion"]