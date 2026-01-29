from ....schemas.dto import BaseModelSdk
from pydantic import ConfigDict
from .type.Bot import Bot as _Bot

class Bot(BaseModelSdk):
    model_config = ConfigDict(title="Notion_Responses_Users_Bot")
    id: str
    type: str = "bot"
    bot: _Bot
    name: str
    avatar_url: str
