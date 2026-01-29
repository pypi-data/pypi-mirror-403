from typing   import Optional, Any
from datetime import datetime

class PropertyExtractor:

    "Classe base com métodos de extração de propriedades do Notion"
    
    def extract(self, prop_data: dict) -> Any:
        
        """
        Extrai o valor de uma propriedade baseado no seu tipo.
        
        Args:
            prop_data: Dicionário com dados da propriedade do Notion
            
        Returns:
            Valor extraído da propriedade ou None
        """

        tipo = prop_data.get("type")
        if not tipo:
            return None
        
        extractors = {
            "title"        : self._title,
            "rich_text"    : self._rich_text,
            "number"       : self._number,
            "checkbox"     : self._checkbox,
            "url"          : self._url,
            "select"       : self._select,
            "multi_select" : self._multi_select,
            "date"         : self._date,
            "relation"     : self._relation,
            "rollup"       : self._rollup,
            "formula"      : self._formula,
        }
        
        extractor = extractors.get(tipo)
        if extractor:
            return extractor(prop_data)
        
        return None
    
    def _title(self, prop_data: dict) -> Optional[str]:
        "Extrai conteúdo de propriedade tipo `title`"
        title = prop_data.get("title")
        if title is None:
            return None
        if isinstance(title, list) and len(title) == 1:
            return title[0]['text'].get('content')
        if isinstance(title, dict):
            return title['text'].get('content')
        content_list = [item['plain_text'] for item in title]
        return "".join(content_list)
    
    def _rich_text(self, prop_data: dict) -> Optional[dict]:
        "Extrai conteúdo de propriedade tipo 'rich_text'"
        prop_list = prop_data.get('rich_text')
        if prop_list is None:
            return None
        content_list = [item['plain_text'] for item in prop_list]
        return {"text": "".join(content_list), "detailed": prop_list}
    
    def _number(self, prop_data: dict) -> Optional[float]:
        "Extrai conteúdo de propriedade tipo 'number'"
        return prop_data.get("number")
    
    def _checkbox(self, prop_data: dict) -> bool:
        "Extrai conteúdo de propriedade tipo 'checkbox'"
        return prop_data.get("checkbox") == True
    
    def _url(self, prop_data: dict) -> Optional[str]:
        "Extrai conteúdo de propriedade tipo 'url'"
        return prop_data.get("url")

    def _select(self, prop_data: dict) -> Optional[dict]:
        "Extrai conteúdo de propriedade tipo 'select'"
        select = prop_data.get("select")
        if not select:
            return None
        return {"name": select.get("name"), "color": select.get("color")}
    
    def _multi_select(self, prop_data: dict) -> Optional[list[dict]]:
        "Extrai conteúdo de propriedade tipo 'multi_select'"
        multi_select = prop_data.get("multi_select")
        if not multi_select:
            return None
        selects = []
        for select in multi_select:
            selects.append(
                {"name": select.get("name"), "color": select.get("color")}
            )
        return selects

    def _date(self, prop_data: dict) -> Optional[dict]:
        "Extrai conteúdo de propriedade tipo 'date'"
        date = prop_data.get("date")
        if not date:
            return None
        
        def parse_date(date_str):
            if not date_str:
                return None
            for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
            return None
        
        start = parse_date(date.get("start"))
        end = parse_date(date.get("end"))
        return {"start": start, "end": end}
    
    def _relation(self, prop_data: dict) -> Optional[list]:
        "Extrai conteúdo de propriedade tipo 'relation'"
        relations = prop_data.get("relation", [])
        if not relations:
            return None
        return [relation["id"] for relation in relations]
    
    def _rollup(self, prop_data: dict) -> Any:
        "Extrai conteúdo de propriedade tipo 'rollup'"
        rollup = prop_data.get("rollup", {})
        rollup_type = rollup.get("type")
        
        if rollup_type == "number":
            return rollup.get("number")
        elif rollup_type == "array":
            return rollup.get("array", [])
        return None
    
    def _formula(self, prop_data: dict) -> Any:
        "Extrai conteúdo de propriedade tipo 'formula'"
        formula = prop_data.get("formula", {})
        formula_type = formula.get("type")
        
        if formula_type == "number":
            return formula.get("number")
        elif formula_type == "string":
            return formula.get("string")
        elif formula_type == "boolean":
            return formula.get("boolean")
        return None

__all__ = ["PropertyExtractor"]