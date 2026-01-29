from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from typing import Optional, List, TypeVar, Generic
from ....orm.mapping.database import NotionDatabase as _NotionDatabase
from ..pages.Page import Page as _Page

TDB = TypeVar('TDB', bound = _NotionDatabase)

class Query(BaseModelSdk, Generic[TDB]):
    model_config = ConfigDict(title="Notion_Responses_Databases_Query")
    results: List[_Page[TDB]]
    next_cursor: Optional[str] = None
    has_more: bool = False
    type: str = "page_or_database"
    page_or_database: dict = {}
