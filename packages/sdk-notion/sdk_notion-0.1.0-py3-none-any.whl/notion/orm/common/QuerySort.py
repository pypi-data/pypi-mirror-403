from typing import Any, Dict, Literal, List

class _NotionSort:
    
    "Classe base para classificação do Notion"
    
    def _sort_to_dict(self) -> Dict[str, Any]:
        "Converte uma classificação para o formato JSON do Notion"
        raise NotImplementedError

    def to_dict(self) -> List[Dict[str, Any]]:
        "Converte uma ou multiplas classificações para o formato JSON do Notion"
        raise NotImplementedError

class _PropertySort(_NotionSort):

    "Classificação para uma propriedade específica"
    
    def __init__(self,
        property_name: str,
        direction: Literal["ascending", "descending"]
    ):
        self.property_name = property_name
        self.direction = direction

    def _sort_to_dict(self) -> Dict[str, Any]:
        return {
            "property": self.property_name,
            "direction": self.direction
        }

    def to_dict(self) -> List[Dict[str, Any]]:
        return [self._sort_to_dict()]

class _MultiSort(_NotionSort):

    "Combina múltiplas classificações com vírgula"
    
    def __init__(self, *sorts: _NotionSort):
        self.sorts = sorts
    
    def to_dict(self) -> List[Dict[str, Any]]:
        return [sort_obj._sort_to_dict() for sort_obj in self.sorts]

class QuerySort:

    "Builder principal para criar filtros"

    @staticmethod
    def and_(*sorts: _NotionSort) -> _MultiSort:
        "Combina classificações com vírgula"
        return _MultiSort(*sorts)

    @staticmethod
    def ascending(
        property_name: str
    ):
        return _PropertySort(
            property_name = property_name,
            direction = "ascending"
        )

    @staticmethod
    def descending(
        property_name: str
    ):
        return _PropertySort(
            property_name = property_name,
            direction = "descending"
        )

__all__ = ["QuerySort"]