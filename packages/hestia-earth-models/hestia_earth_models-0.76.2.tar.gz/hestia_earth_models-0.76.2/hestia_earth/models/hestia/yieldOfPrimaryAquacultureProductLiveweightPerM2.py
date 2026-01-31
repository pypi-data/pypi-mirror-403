from hestia_earth.schema import TermTermType
from hestia_earth.utils.model import find_primary_product
from hestia_earth.utils.tools import list_sum

from hestia_earth.models.log import logRequirements, logShouldRun
from hestia_earth.models.utils.practice import _new_practice
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "siteArea": "",
        "products": [
            {
                "@type": "Product",
                "primary": "True",
                "term.termType": "liveAquaticSpecies",
            }
        ],
    }
}
RETURNS = {"Practice": [{"value": ""}]}
TERM_ID = "yieldOfPrimaryAquacultureProductLiveweightPerM2"


def _run(product: dict, site_area: float):
    return [
        _new_practice(
            model=MODEL,
            term=TERM_ID,
            value=list_sum(product.get("value")) / (site_area * 10000),
        )
    ]


def _should_run(cycle: dict):
    product = find_primary_product(cycle)
    is_live_aquatic_species = (product or {}).get("term", {}).get(
        "termType"
    ) == TermTermType.LIVEAQUATICSPECIES.value
    has_value = list_sum((product or {}).get("value"), default=None) is not None
    site_area = cycle.get("siteArea")

    logRequirements(
        cycle,
        model=MODEL,
        term=TERM_ID,
        is_live_aquatic_species=is_live_aquatic_species,
        has_value=has_value,
        has_site_area=site_area is not None,
    )

    should_run = all([site_area is not None, is_live_aquatic_species, has_value])
    logShouldRun(cycle, MODEL, TERM_ID, should_run)
    return should_run, product, site_area


def run(cycle: dict):
    should_run, product, site_area = _should_run(cycle)
    return _run(product, site_area) if should_run else []
