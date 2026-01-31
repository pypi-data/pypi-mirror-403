import os
from hestia_earth.schema import TermTermType
from hestia_earth.utils.lookup import download_lookup, get_table_value
from hestia_earth.utils.tools import safe_parse_float

LOOKUP_MAPPING_KEY = "ecoalimMapping"
LOOKUP_NAME_PREFIX = "ecoalim-"
LOOKUP_INDEX_KEY = "ecoalimMappingName"
CUTOFF_MAX_PERCENTAGE = int(os.getenv("ECOALIM_CUTOFF_MAX_PERCENT", "99"))


def _get_cutoff_lookup(term_type: TermTermType):
    filename = f"ecoalim-{term_type.value}-cutoff.csv"
    return download_lookup(filename) if CUTOFF_MAX_PERCENTAGE else None


def cutoff_value(cutoff_id: str) -> float:
    cutoff_lookup = _get_cutoff_lookup(term_type=TermTermType.EMISSION)
    return (
        None
        if cutoff_lookup is None
        else safe_parse_float(
            get_table_value(cutoff_lookup, "term.id", cutoff_id, "percentage"),
            default=None,
        )
    )
