from typing   import Literal, Any, Optional
from pydantic import validate_call
from ....schemas.responses.pages.Page   import Page        as _schmPage
from ....schemas.responses.errors.Error import Error       as _schmError
from ....client                         import get_client  as _get_client
from ...common.SetProperty import SetProperty as _setProperty
from ...parsers            import Parser      as _parser

class CreatePage:

    def __init__(self) -> None:
        self.data : dict[str, Any] = {
            "properties": {}
        }
        self.set_property = _setProperty(self, self.data["properties"])

    @validate_call
    def set_parent(self,
        type      : Literal["page_id", "database_id"],
        parent_id : str
    ):
        
        self.data["parent"] = {
            type : parent_id
        }

        return self

    @validate_call
    def set_template(self,
        type        : Literal["default", "template_id"],
        template_id : Optional[str] = None
    ):

        if type == "template_id":
            if template_id is None:
                raise TypeError("Template Type was set to 'template_id' but no ID was provided")
            self.data["template"] = {
                "type": type,
                "template_id": template_id
            }
            return self

        self.data["template"] = {
            "type": type
        }

        return self

    @validate_call
    def set_title(self,
        prop_name  : Optional[str],
        prop_value : Optional[str]
    ):

        if prop_value is None:
            return self

        if self.data["parent"].get("page_id"):

            self.data["properties"] = {
                "title": [
                    {
                        "text": {
                            "content": prop_value
                        }
                    }
                ]
            }

            return self

        self.data["properties"][prop_name] = {
            "title": [
                {
                    "text": {
                        "content": prop_value
                    }
                }
            ]
        }

        return self

    @validate_call
    def set_icon(self,
        type: Literal["external"],
        content: Optional[str]
    ):

        if content is None:
            return self

        match type:

            case "external":
                self.data["icon"] = {
                    "external": {
                        "url": str(content)
                    }
                }

        return self

    @validate_call
    def set_children(self,
        type: Literal["heading_1", "paragraph"],
        content: Any
    ):
        
        if self.data.get("children") is None:
            self.data["children"] = []

        match type:

            case "heading_1":
                self.data["children"].append(
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                )

            case "paragraph":
                self.data["children"].append(
                    {                        
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                )

        return self

    async def call(self,
        parse_properties : bool = True
    ) -> _schmPage:
        
        client = _get_client()

        create = await client.pages.create(
            json_data = self.data
        )

        if create['object'] == 'error':
            error = _schmError(**create)
            raise KeyError(error.__dict__)

        if parse_properties:

            properties = _parser.page_props(page = create)

            create["properties"] = properties

        return _schmPage(**create)

__all__ = ["CreatePage"]