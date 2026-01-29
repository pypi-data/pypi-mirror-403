from .....schemas.dto import BaseModelSdk
from pydantic import ConfigDict

class Person(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Users_Type_Person")
    email: str
