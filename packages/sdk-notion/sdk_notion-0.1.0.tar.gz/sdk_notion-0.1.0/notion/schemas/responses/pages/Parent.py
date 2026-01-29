from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from typing   import Optional, Literal

class Parent(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Pages_Parent")
    type: Literal ["page_id", "data_source_id", "database_id"]
    data_source_id: Optional[str] = None
    database_id: Optional[str] = None
