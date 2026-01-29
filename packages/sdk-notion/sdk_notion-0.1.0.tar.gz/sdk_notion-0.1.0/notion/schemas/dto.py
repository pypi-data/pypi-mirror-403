from pydantic import BaseModel, ConfigDict
from datetime import datetime, date

class BaseModelSdk(BaseModel):

    "Pydantic BaseModel com configuraçoes Padronizadas para o SDK"
    
    model_config = ConfigDict(
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
            date: lambda v: v.strftime("%Y-%m-%d")
        }
    )
