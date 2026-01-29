from .....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from typing   import Dict, Any, Optional

class RichText(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Pages_Properties_RichText")
    type: str
    text: 'Text'
    annotations: 'Annotations'
    plain_text: Optional[str]
    href: Optional[str]

    class Text(BaseModelSdk):
        content: Optional[str]
        link: Optional[str]
    
    class Annotations(BaseModelSdk):
        bold: bool
        italic: bool
        strikethrough: bool
        underline: bool
        code: bool
        color: str
