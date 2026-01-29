from typing import Literal, Union

def headers(
    api_token   : str,
    api_version : Union[Literal["legacy", "data_sources"], str] = "data_sources"
):
    
    match api_version:
        case "legacy":
            version = "2022-06-28"
        case "data_sources":
            version = "2025-09-03"
        case _:
            version = api_version
    
    headers = {
        "Authorization"  : f"Bearer {api_token}",
        "Content-Type"   : "application/json",
        "Notion-Version" : version
    }
    
    return headers
