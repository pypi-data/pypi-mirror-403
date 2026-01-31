from hestia_earth.schema import SiteSiteType, TermTermType
from hestia_earth.utils.model import find_term_match, filter_list_term_type
from hestia_earth.utils.tools import list_sum

from hestia_earth.models.log import logRequirements, log_as_table
from hestia_earth.models.utils.lookup import depreciated_id
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "or": [
            {
                "site": {"@type": "Site", "siteType": ["cropland"]},
                "inputs": [
                    {
                        "@type": "Input",
                        "value": "",
                        "term.@id": "machineryInfrastructureDepreciatedAmountPerCycle",
                    }
                ],
            },
            {
                "site": {
                    "@type": "Site",
                    "siteType": ["glass or high accessible cover"],
                    "infrastructure": [
                        {
                            "@type": "Infrastructure",
                            "term.termType": "building",
                            "inputs": [
                                {
                                    "@type": "Input",
                                    "value": "",
                                    "term.termType": ["material", "substrate"],
                                }
                            ],
                        }
                    ],
                },
                "inputs": [
                    {
                        "@type": "Input",
                        "value": "",
                        "term.termType": ["material", "substrate"],
                    }
                ],
            },
        ]
    }
}
RETURNS = {"Completeness": {"material": ""}}
MODEL_KEY = "material"


def _run_cropland(cycle: dict):
    machinery_input = find_term_match(
        cycle.get("inputs", []), "machineryInfrastructureDepreciatedAmountPerCycle", {}
    )
    has_machinery_input = machinery_input and len(machinery_input.get("value", [])) > 0

    logRequirements(
        cycle,
        model=MODEL,
        term=None,
        key=MODEL_KEY,
        is_cropland=True,
        has_machinery_input=has_machinery_input,
    )

    return all([has_machinery_input])


def _infrastructure_input_data(cycle_inputs: list, input: dict):
    term = input.get("term", {})
    depreciated_term_id = depreciated_id(term)
    cycle_depreciated_input = find_term_match(cycle_inputs, depreciated_term_id, {})
    cycle_depreciated_input_value = list_sum(
        cycle_depreciated_input.get("value"), default=None
    )
    valid = all([cycle_depreciated_input, cycle_depreciated_input_value is not None])

    return {
        "valid": valid,
        "input-term-id": term.get("@id"),
        "input-depreciated-id": depreciated_term_id,
        "input-depreciated-value": cycle_depreciated_input_value,
    }


def _infrastructure_data(cycle_inputs: list, infrastructure: dict):
    inputs = filter_list_term_type(
        infrastructure.get("inputs", []),
        [TermTermType.MATERIAL, TermTermType.SUBSTRATE],
    )
    input_values = [_infrastructure_input_data(cycle_inputs, i) for i in inputs]
    invalid_inputs = [i for i in input_values if not i["valid"]]

    valid = len(invalid_inputs) == 0

    return {
        "valid": valid,
        "infrastructure-id": infrastructure.get("term", {}).get("@id"),
        "inputs-missing-depreciated-with-value": ";".join(
            [i["input-term-id"] for i in invalid_inputs]
        ),
    }


def _run_greenhouse(cycle: dict):
    inputs = filter_list_term_type(
        cycle.get("inputs", []), [TermTermType.MATERIAL, TermTermType.SUBSTRATE]
    )
    site = cycle.get("site", {})

    infrastructure = filter_list_term_type(
        site.get("infrastructure", []), TermTermType.BUILDING
    )
    infrastructure_values = [_infrastructure_data(inputs, i) for i in infrastructure]

    logRequirements(
        cycle,
        model=MODEL,
        term=None,
        key=MODEL_KEY,
        infrastructure_values=log_as_table(infrastructure_values),
    )

    return any([not infrastructure, all([i["valid"] for i in infrastructure_values])])


_RUN_BY_SITE_TYPE = {
    SiteSiteType.CROPLAND.value: _run_cropland,
    SiteSiteType.GLASS_OR_HIGH_ACCESSIBLE_COVER.value: _run_greenhouse,
}


def run(cycle: dict):
    site_type = cycle.get("site", {}).get("siteType")
    return _RUN_BY_SITE_TYPE.get(site_type, lambda *args: False)(cycle)
