from typing   import Dict, Any, Union, Optional, Literal, List, TYPE_CHECKING
from datetime import datetime, date
from pydantic import validate_call
from ..config import ORMConfig

if TYPE_CHECKING:
    from ..repositories.pages.CreatePage import CreatePage
    from ..repositories.databases.CreateDatabasePage import CreateDatabasePage

class SetProperty:

    def __init__(self,
        CreatePageClass : Union['CreatePage', 'CreateDatabasePage'],
        properties : Dict[str, Any]
    ) -> None:
        self._CreatePage = CreatePageClass
        self._properties = properties

    @validate_call
    def number(self,
        name  : str,
        value : Optional[float]
    ):
        if value is None:
            return self._CreatePage
        self._properties[name] = {
            "number": value
        }
        return self._CreatePage
    
    @validate_call
    def checkbox(self,
        name  : str,
        value : Optional[bool]
    ):
        if value is None:
            return self._CreatePage
        self._properties[name] = {
            "checkbox": value
        }
        return self._CreatePage
    
    @validate_call
    def start_date(self,
        name  : str,
        value : Optional[Union[date, datetime]],
        timezone : Optional[str] = None
    ):
        timezone = timezone if timezone is not None else ORMConfig.get_timezone()
        if value is None:
            return self._CreatePage
        if type(value) == date:
            self._properties[name] = {
                "date": {
                    "start": value.strftime("%Y-%m-%d")
                }
            }
        elif type(value) == datetime:
            self._properties[name] = {
                "date": {
                    "start": value.strftime("%Y-%m-%dT%H:%M:%S"),
                    "time_zone": timezone
                }
            }
        return self._CreatePage

    @validate_call
    def end_date(self,
        name  : str,
        value : Optional[Union[date, datetime]]
    ):
        if value is None:
            return self._CreatePage
        if not self._properties.get(name):
            raise KeyError("start_date is missing")
        date_value = None
        if type(value) == date:
            date_value = value.strftime("%Y-%m-%d")
        elif type(value) == datetime:
            date_value = value.strftime("%Y-%m-%dT%H:%M:%S")
        self._properties[name]["date"]["end"] = date_value
        return self._CreatePage

    @validate_call
    def relation(self,
        name  : str,
        value : Optional[str]
    ):
        if value is None:
            return self._CreatePage
        self._properties[name] = {
            "relation": [
                {
                    "id": str(value)
                }
            ]
        }
        return self._CreatePage
    
    @validate_call
    def text(self,
        name  : str,
        value : Optional[str]
    ):
        if value is None:
            return self._CreatePage
        self._properties[name] = {
            "rich_text" : [
                {
                    "type":"text",
                    "text":{
                        "content": value
                    }
                }
            ]
        }
        return self._CreatePage

    @validate_call
    def rich_text(self,
        name  : str,
        value : Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]
    ):
        if value is None:
            return self._CreatePage
        value = [value] if isinstance(value, dict) else value
        self._properties[name] = {
            "rich_text" : value
        }
        return self._CreatePage

    @validate_call
    def select(self,
        name  : str,
        value : Optional[str],
        color : Optional[Literal[
            "default",
            "gray",
            "brown",
            "orange",
            "yellow",
            "green",
            "blue",
            "purple",
            "pink",
            "red"
        ]] = None
    ):
        if value is None:
            return self._CreatePage
        if color:
            self._properties[name] = {
                "select" : {
                    "name" : value,
                    "color" : color
                }
            }
            return self._CreatePage
        self._properties[name] = {
            "select" : {
                "name" : value
            }
        }
        return self._CreatePage

    # @validate_call
    # def multi_select(self, name : str, value : str):

    # @validate_call
    # def status(self, name : str, value : str):

    # @validate_call
    # def media(self, name : str, value : str):

    @validate_call
    def url(self,
        name  : str,
        value : Optional[str]
    ):
        if value is None:
            return self._CreatePage
        self._properties[name] = {
            "url" : value
        }
        return self._CreatePage

    @validate_call
    def email(self,
        name  : str,
        value : Optional[str]
    ):
        if value is None:
            return self._CreatePage
        if "@" not in value:
            raise ValueError("Invalid email")
        self._properties[name] = {
            "email": str(value)
        }
        return self._CreatePage
    
    @validate_call
    def phone(self,
        name  : str,
        value : Optional[str]
    ):
        if value is None:
            return self._CreatePage
        self._properties[name] = {
            "phone_number": str(value)
        }
        return self._CreatePage
    
    @validate_call
    def person(self,
        name  : str,
        value : Optional[str]
    ):
        if value is None:
            return self._CreatePage
        self._properties[name] = {
            "people": [
                {
                    "object": "user",
                    "id": str(value)
                }
            ]
        }
        return self._CreatePage
    
    # @validate_call
    # def place(self, name : str, value : str):

__all__ = ["SetProperty"]