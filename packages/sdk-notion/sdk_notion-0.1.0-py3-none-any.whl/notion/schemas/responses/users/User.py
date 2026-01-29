from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict

class User(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Users_User")
    id: str
