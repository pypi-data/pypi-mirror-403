from typing import Optional, Union, List
from hestia_earth.schema import TermTermType
from hestia_earth.utils.term import download_term

from .constant import DEFAULT_COUNTRY_ID


def get_parent_region(country_term: Union[str, dict]) -> Optional[str]:
    term = download_term(country_term, TermTermType.REGION)
    return (term or {}).get("subClassOf", [{}])[0].get("@id")


def get_parent_regions(country: Union[str, dict]) -> List[str]:
    current = get_parent_region(country) if country != DEFAULT_COUNTRY_ID else None
    return (
        [current]
        + (get_parent_regions(current) if current != DEFAULT_COUNTRY_ID else [])
        if current
        else []
    )
