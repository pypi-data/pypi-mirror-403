from functools import lru_cache
from hestia_earth.utils.lookup import load_lookup

from hestia_earth.models.data.ecoinventV3 import get_filepath
from hestia_earth.models.utils.background_data import convert_background_lookup

LOOKUP_MAPPING_KEY = "ecoinventMapping"
_LOOKUP_INDEX_KEY = "ecoinventName"


@lru_cache()
def build_lookup(term_type: str):
    filepath = get_filepath(term_type)
    lookup = load_lookup(filepath=filepath, keep_in_memory=False)
    return convert_background_lookup(lookup=lookup, index_column=_LOOKUP_INDEX_KEY)
