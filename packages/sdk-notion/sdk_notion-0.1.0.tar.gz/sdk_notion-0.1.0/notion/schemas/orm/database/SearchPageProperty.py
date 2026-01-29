from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from typing   import Any, Optional

class SearchPageProperty(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Orm_Database_SearchPageProperty")
    page_id : str
    prop_value : Optional[Any] = None
