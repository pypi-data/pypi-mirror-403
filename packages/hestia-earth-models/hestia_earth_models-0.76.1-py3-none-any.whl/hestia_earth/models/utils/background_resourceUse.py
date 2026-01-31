from typing import List, Optional, Union
from hestia_earth.schema import UNIQUENESS_FIELDS, SchemaType, TermTermType
from hestia_earth.utils.tools import flatten, list_sum, non_empty_list
from hestia_earth.utils.blank_node import group_by_keys

from hestia_earth.models.log import logShouldRun, logRequirements
from .indicator import _new_indicator
from .background_data import (
    LookupValuesType,
    get_background_inputs,
    no_gap_filled_background_emissions,
    log_missing_emissions,
    parse_term_id,
    get_input_mappings,
    process_input_mappings,
)
from .impact_assessment import get_product, convert_value_from_cycle

MODEL_KEY = "impact_assessment"
_UNIQUE_FIELDS = [
    v.split(".")[0]
    for v in UNIQUENESS_FIELDS[SchemaType.IMPACTASSESSMENT.value][
        "emissionsResourceUse"
    ]
]


def _indicator(
    model: str,
    term_id: str,
    value: float,
    input: dict,
    country_id: str = None,
    key_id: str = None,
    land_cover_id: str = None,
    previous_land_cover_id: str = None,
):
    indicator = _new_indicator(
        term=term_id,
        value=value,
        model=model,
        land_cover_id=land_cover_id,
        previous_land_cover_id=previous_land_cover_id,
        country_id=country_id,
        key_id=key_id,
        inputs=[input.get("term")],
    )
    if indicator:
        if input.get("operation"):
            indicator["operation"] = input.get("operation")
        if input.get("animal"):
            indicator["animals"] = [input.get("animal")]
    return indicator


def _run_input(
    model: str,
    impact_assessment: dict,
    lookup_mapping_key: str,
    lookup_values: LookupValuesType,
    filter_by_country: bool = False,
):
    no_gap_filled_background_emissions_func = no_gap_filled_background_emissions(
        node=impact_assessment,
        list_key="emissionsResourceUse",
        term_type=TermTermType.RESOURCEUSE,
    )
    log_missing_emissions_func = log_missing_emissions(
        impact_assessment, TermTermType.RESOURCEUSE, model=model
    )
    product = get_product(impact_assessment)

    def run(inputs: list):
        input = inputs[0]
        input_term_id = input.get("term", {}).get("@id")
        input_value = list_sum(flatten(input.get("value", []) for input in inputs))
        mappings = get_input_mappings(
            model, input, lookup_mapping_key, filter_by_country=filter_by_country
        )
        has_mappings = len(mappings) > 0

        # grouping the inputs together in the logs
        input_parent_term_id = (input.get("parent", {})).get("@id") or input.get(
            "animalId", {}
        )
        extra_logs = {
            **(
                {"input_group_id": input_parent_term_id} if input_parent_term_id else {}
            ),
            **({"animalId": input.get("animalId")} if input.get("animalId") else {}),
        }

        # skip input that has background emissions we have already gap-filled (model run before)
        has_no_gap_filled_background_resourceUses = (
            no_gap_filled_background_emissions_func(input)
        )

        logRequirements(
            impact_assessment,
            model=model,
            term=input_term_id,
            model_key=MODEL_KEY,
            has_mappings=has_mappings,
            mappings=";".join([v["name"] for v in mappings]),
            has_no_gap_filled_background_resourceUses=has_no_gap_filled_background_resourceUses,
            input_value=input_value,
            **extra_logs
        )

        should_run = all(
            [has_mappings, has_no_gap_filled_background_resourceUses, input_value]
        )
        logShouldRun(
            impact_assessment,
            model,
            input_term_id,
            should_run,
            model_key=MODEL_KEY,
            **extra_logs
        )

        results = (
            process_input_mappings(
                impact_assessment,
                input,
                mappings,
                TermTermType.RESOURCEUSE,
                lookup_values,
                **(extra_logs | {"model": model, "model_key": MODEL_KEY})
            )
            if should_run
            else {}
        )
        has_no_gap_filled_background_resourceUses and log_missing_emissions_func(
            input_term_id,
            list(map(parse_term_id, results.keys())),
            **(extra_logs | {"has_mappings": has_mappings})
        )
        return non_empty_list(
            [
                _indicator(
                    model=model,
                    term_id=parse_term_id(term_id),
                    value=convert_value_from_cycle(
                        product,
                        sum([v["value"] * v["coefficient"] for v in values])
                        * input_value,
                    ),
                    input=input,
                    country_id=values[0].get("country"),
                    key_id=values[0].get("key"),
                    land_cover_id=values[0].get("landCover"),
                    previous_land_cover_id=values[0].get("previousLandCover"),
                )
                for term_id, values in results.items()
            ]
        )

    return run


def run(
    model: str,
    impact_assessment: dict,
    lookup_mapping_key: str,
    lookup_values: LookupValuesType,
    filter_term_types: Optional[Union[TermTermType, List[TermTermType]]] = [],
    filter_by_country: bool = False,
):
    inputs = get_background_inputs(
        impact_assessment.get("cycle", {}), filter_term_types=filter_term_types
    )
    grouped_inputs = group_by_keys(inputs, ["term", "operation", "animal"])
    resource_uses = flatten(
        map(
            _run_input(
                model,
                impact_assessment,
                lookup_mapping_key,
                lookup_values,
                filter_by_country,
            ),
            grouped_inputs.values(),
        )
    )
    # group the resourceUse again to make sure we do not return duplicated resourceUse
    grouped_resource_uses = group_by_keys(resource_uses, _UNIQUE_FIELDS)
    return [
        resource_uses[0]
        | {"value": list_sum(flatten([v["value"] for v in resource_uses]))}
        for resource_uses in grouped_resource_uses.values()
    ]
