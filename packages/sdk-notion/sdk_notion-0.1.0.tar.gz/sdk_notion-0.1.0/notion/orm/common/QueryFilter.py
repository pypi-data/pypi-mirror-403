from typing   import Any, Dict, Literal, Union
from datetime import datetime, date

class _NotionFilter:
    
    "Classe base para filtros do Notion"
    
    def to_dict(self) -> Dict[str, Any]:
        "Converte o filtro para o formato JSON do Notion"
        raise NotImplementedError
    
    def and_(self, *filters: '_NotionFilter') -> '_NotionFilter':
        "Combina este filtro com outros usando AND"
        return _AndFilter(self, *filters)
    
    def or_(self, *filters: '_NotionFilter') -> '_NotionFilter':
        "Combina este filtro com outros usando OR"
        return _OrFilter(self, *filters)

class _PropertyFilter(_NotionFilter):

    "Filtro para uma propriedade específica"
    
    def __init__(self,
        property_name: str,
        property_type: str, 
        condition: str,
        value: Any
    ):
        self.property_name = property_name
        self.property_type = property_type
        self.condition = condition
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "property": self.property_name,
            self.property_type: {
                self.condition: self.value
            }
        }

class _AndFilter(_NotionFilter):

    "Combina múltiplos filtros com AND"
    
    def __init__(self, *filters: _NotionFilter):
        self.filters = list(filters)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "and": [filter_obj.to_dict() for filter_obj in self.filters]
        }

class _OrFilter(_NotionFilter):

    "Combina múltiplos filtros com OR"
    
    def __init__(self, *filters: _NotionFilter):
        self.filters = list(filters)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "or": [filter_obj.to_dict() for filter_obj in self.filters]
        }

class QueryFilter:

    "Builder principal para criar filtros"

    @staticmethod
    def and_(*filters: _NotionFilter) -> _AndFilter:
        "Combina filtros com AND"
        return _AndFilter(*filters)
    
    @staticmethod
    def or_(*filters: _NotionFilter) -> _OrFilter:
        "Combina filtros com OR"
        return _OrFilter(*filters)

    @staticmethod
    def created_time(
        property_name: str,
        condition: Literal[
            "equals",
            "before",
            "after",
            "on_or_before",
            "on_or_after",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[date, Literal[True]]
    ):
        if isinstance(value, date):
            property_value = value.strftime("%Y-%m-%d")
        else:
            property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "created_time",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def last_edited_time(
        property_name: str,
        condition: Literal[
            "equals",
            "before",
            "after",
            "on_or_before",
            "on_or_after",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[date, Literal[True]]
    ):
        if isinstance(value, date):
            property_value = value.strftime("%Y-%m-%d")
        else:
            property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "last_edited_time",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def title(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "contains",
            "does_not_contain",
            "starts_with",
            "ends_with",
            "is_empty",
            "is_not_empty"
        ],
        value: str
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "title",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def rich_text(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "contains",
            "does_not_contain",
            "starts_with",
            "ends_with",
            "is_empty",
            "is_not_empty"
        ],
        value: str
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "rich_text",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def number(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "greater_than",
            "less_than",
            "greater_than_or_equal_to",
            "less_than_or_equal_to",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[float, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "number",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def checkbox(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal"
        ],
        value: Literal[True]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "checkbox",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def select(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "select",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def multi_select(
        property_name: str,
        condition: Literal[
            "contains",
            "does_not_contain",
            "equals",
            "does_not_equal",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "multi_select",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def status(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "status",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def dates(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "after",
            "on_or_before",
            "on_or_after",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[date, datetime, Literal[True]]
    ):
        if isinstance(value, date):
            property_value = value.strftime("%Y-%m-%d")
        elif isinstance(value, datetime):
            property_value = value.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "date",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def people(
        property_name: str,
        condition: Literal[
            "contains",
            "does_not_contain",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "people",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def files(
        property_name: str,
        condition: Literal[
            "is_empty",
            "is_not_empty"
        ],
        value: Literal[True]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "files",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def url(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "contains",
            "does_not_contain",
            "starts_with",
            "ends_with",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "url",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def email(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "contains",
            "does_not_contain",
            "starts_with",
            "ends_with",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "email",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def phone_number(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "contains",
            "does_not_contain",
            "starts_with",
            "ends_with",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "phone_number",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def relation(
        property_name: str,
        condition: Literal[
            "contains",
            "does_not_contain",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "relation",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def created_by(
        property_name: str,
        condition: Literal[
            "contains",
            "does_not_contain",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "created_by",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def last_edited_by(
        property_name: str,
        condition: Literal[
            "contains",
            "does_not_contain",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[str, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "last_edited_by",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def formula(
        property_name: str,
        formula_type: Literal["string", "checkbox", "number", "date"],
        condition: Literal[
            "equals",
            "does_not_equal",
            "contains",
            "does_not_contain",
            "starts_with",
            "ends_with",
            "is_empty",
            "is_not_empty",
            "greater_than",
            "less_than",
            "greater_than_or_equal_to",
            "less_than_or_equal_to",
            "before",
            "after",
            "on_or_before",
            "on_or_after"
        ],
        value: Union[str, bool, float, date, datetime, Literal[True]]
    ) -> _PropertyFilter:
        if isinstance(value, date):
            property_value = value.strftime("%Y-%m-%d")
        elif isinstance(value, datetime):
            property_value = value.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = f"formula.{formula_type}",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def unique_id(
        property_name: str,
        condition: Literal[
            "equals",
            "does_not_equal",
            "greater_than",
            "less_than",
            "greater_than_or_equal_to",
            "less_than_or_equal_to",
            "is_empty",
            "is_not_empty"
        ],
        value: Union[float, Literal[True]]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "unique_id",
            condition     = condition,
            value         = property_value
        )

    @staticmethod
    def verification(
        property_name: str,
        condition: Literal[
            "status"
        ],
        value: Literal["verified", "expired", "none", ""]
    ):
        property_value = value
        return _PropertyFilter(
            property_name = property_name,
            property_type = "verification",
            condition     = condition,
            value         = property_value
        )

__all__ = ["QueryFilter"]