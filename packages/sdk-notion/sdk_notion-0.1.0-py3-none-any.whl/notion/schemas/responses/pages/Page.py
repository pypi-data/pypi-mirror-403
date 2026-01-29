from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from typing   import Optional, Any, Dict, Generic, TypeVar, Union
from datetime import datetime
from ....orm.mapping.database import NotionDatabase as _NotionDatabase
from ..users.User import User as _User
from .Parent import Parent as _Parent

TDB = TypeVar('TDB', bound = _NotionDatabase)

class Page(BaseModelSdk, Generic[TDB]):
    model_config = ConfigDict(title="Notion_Responses_Pages_Page")
    id: str
    created_time: datetime
    last_edited_time: datetime
    created_by: _User
    last_edited_by: _User
    cover: Optional[Dict[str, Any]]
    icon: Optional[Dict[str, Any]]
    parent: _Parent
    archived: bool
    properties: Union[Any, TDB]
    url: str
    public_url: Optional[str]
