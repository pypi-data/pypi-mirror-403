from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from typing   import Dict, Any, List, Optional
from ...responses.pages.properties.RichText import RichText as _RichText

class RichText(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Orm_Common_RichText")
    text: Optional[str]
    detailed: List[_RichText]
