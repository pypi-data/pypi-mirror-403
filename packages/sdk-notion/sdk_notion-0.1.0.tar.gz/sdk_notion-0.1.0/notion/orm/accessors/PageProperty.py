from typing import Any, Optional
from pydantic import validate_call
from ..extrators.Properties import PropertyExtractor

class _PageProperty(PropertyExtractor):

    "Getter específico para propriedades individuais do Notion. Permite buscar uma propriedade específica por nome e tipo."

    def _get_properties_dict(self, response: dict) -> dict:
        "Extrai o dicionário de properties do response"
        nt_dict = response.get('properties')
        if nt_dict is None:
            nt_dict = response.get('result')
            if nt_dict is None:
                raise KeyError("Response inserido é inválido")
        return nt_dict
    
    def _get_property_data(self, response: dict, name: str, expected_type: str) -> dict:
        
        """
        Busca e valida uma propriedade específica.
        
        Args:
            response: Response completo do Notion
            name: Nome da propriedade
            expected_type: Tipo esperado da propriedade
            
        Returns:
            Dados da propriedade
            
        Raises:
            KeyError: Se propriedade não existe
            ValueError: Se tipo não corresponde
        """

        properties = self._get_properties_dict(response)
        
        prop = properties.get(name)
        if not prop:
            raise KeyError(f"Propriedade '{name}' não foi encontrada")
        
        actual_type = prop.get('type')
        if actual_type != expected_type:
            raise ValueError(
                f"Propriedade '{name}' não é do tipo '{expected_type}' "
                f"(tipo atual: '{actual_type}')"
            )
        
        return prop
    
    # ==================== CLASSES INTERNAS ====================
       
    @validate_call
    def id(self, response: dict) -> str:
        prop = response.get('id')
        if not prop:
            raise KeyError("ID da página não foi encontrada")
        return prop

    @validate_call
    def title(self, response: dict, name: str) -> Optional[str]:
        prop = self._get_property_data(response, name, "title")
        return self._title(prop)
     
    @validate_call
    def text(self, response: dict, name: str) -> Optional[dict]:
        prop = self._get_property_data(response, name, "rich_text")
        return self._rich_text(prop)
     
    @validate_call
    def number(self, response: dict, name: str) -> Optional[float]:
        prop = self._get_property_data(response, name, "number")
        return self._number(prop)

    @validate_call
    def select(self, response: dict, name: str) -> Optional[dict]:
        prop = self._get_property_data(response, name, "select")
        return self._select(prop)
    
    @validate_call
    def checkbox(self, response: dict, name: str) -> bool:
        prop = self._get_property_data(response, name, "checkbox")
        return self._checkbox(prop)

    @validate_call
    def date(self, response: dict, name: str) -> Optional[dict]:
        prop = self._get_property_data(response, name, "date")
        return self._date(prop)
    
    @validate_call
    def relation(self, response: dict, name: str) -> Optional[list]:
        prop = self._get_property_data(response, name, "relation")
        return self._relation(prop)
    
    @validate_call
    def rollup(self, response: dict, name: str) -> Any:
        prop = self._get_property_data(response, name, "rollup")
        return self._rollup(prop)

    @validate_call
    def formula(self, response: dict, name: str) -> Any:
        prop = self._get_property_data(response, name, "formula")
        return self._formula(prop)

PageProperty = _PageProperty()
__all__ = ['_PageProperty']