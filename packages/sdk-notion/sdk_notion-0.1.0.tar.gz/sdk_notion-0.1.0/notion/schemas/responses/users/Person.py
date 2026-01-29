from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from .type.Person import Person as _Person

class Person(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Users_Person")
    id: str
    type: str = "person"
    person: _Person
    name: str
    avatar_url: str
