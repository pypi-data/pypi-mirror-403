from typing import Optional, Dict, Any
from urllib.parse import unquote
from ..extrators.Properties import PropertyExtractor as _PropertyExtractor

class _PageProperties(_PropertyExtractor):

    "Parser completo de página do Notion. Retorna todas as propriedades parseadas de uma vez."
    
    def parse(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
     
        result = {}
        
        if page.get("object") == "property_item":

            value = self.extract(page)

            if value is not None:
                result[unquote(page["id"])] = value

            return result

        properties = page.get("properties")
        
        if not properties:
            return None

        for prop_name, prop_data in properties.items():
            value = self.extract(prop_data)
            
            if value is not None:
                result[prop_name] = value
        
        return result

PageProperties = _PageProperties()
__all__ = ["PageProperties"]