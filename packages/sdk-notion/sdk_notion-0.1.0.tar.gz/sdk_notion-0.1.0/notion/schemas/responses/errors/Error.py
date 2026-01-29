from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict

class Error(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Errors_Error")
    status: int
    code: str
    message: str
