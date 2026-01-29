from .....schemas.dto import BaseModelSdk
from pydantic import ConfigDict

class Bot(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Users_Type_Bot")
    ...
