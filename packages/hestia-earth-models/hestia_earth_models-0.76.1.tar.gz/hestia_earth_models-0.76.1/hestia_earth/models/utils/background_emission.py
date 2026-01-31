from typing import List, Optional, Union, Callable
from hestia_earth.schema import (
    UNIQUENESS_FIELDS,
    SchemaType,
    EmissionMethodTier,
    TermTermType,
)
from hestia_earth.utils.blank_node import group_by_keys
from hestia_earth.utils.tools import flatten, list_sum, non_empty_list

from hestia_earth.models.log import logShouldRun, logRequirements
from .background_data import (
    LookupValuesType,
    CutoffValueFunc,
    CUTOFF_KEY,
    get_background_inputs,
    no_gap_filled_background_emissions,
    log_missing_emissions,
    parse_term_id,
    get_input_mappings,
    process_input_mappings,
    cutoff_id,
    filter_blank_nodes_cutoff,
)
from .emission import _new_emission
from .fertiliser import get_fertilisers_from_inputs
from .pesticideAI import get_pesticides_from_inputs

MODEL_KEY = "cycle"
_UNIQUE_FIELDS = [
    v.split(".")[0] for v in UNIQUENESS_FIELDS[SchemaType.CYCLE.value]["emissions"]
]
TIER = EmissionMethodTier.BACKGROUND.value


def _emission(
    model: str,
    term_id: str,
    value: float,
    input: dict,
    country_id: str = None,
    key_id: str = None,
    cutoff_value_func: Callable[[str], float] = None,
):
    emission = _new_emission(
        term=term_id, model=model, value=value, country_id=country_id, key_id=key_id
    )
    emission["methodTier"] = TIER
    emission["inputs"] = [input.get("term")]
    if input.get("operation"):
        emission["operation"] = input.get("operation")
    if input.get("animal"):
        emission["animals"] = [input.get("animal")]
    cutoff = (
        cutoff_value_func(
            cutoff_id(term_id=term_id, country_id=country_id, key_id=key_id)
        )
        if cutoff_value_func
        else None
    )
    return emission | ({CUTOFF_KEY: value * cutoff} if cutoff is not None else {})


def _run_input(
    model: str,
    cycle: dict,
    lookup_mapping_key: str,
    lookup_values: LookupValuesType,
    filter_by_country: bool,
    cutoff_value_func: CutoffValueFunc = None,
):
    no_gap_filled_background_emissions_func = no_gap_filled_background_emissions(cycle)
    log_missing_emissions_func = log_missing_emissions(
        cycle, model=model, methodTier=TIER
    )

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
        has_no_gap_filled_background_emissions = (
            no_gap_filled_background_emissions_func(input)
        )

        logRequirements(
            cycle,
            model=model,
            term=input_term_id,
            model_key=MODEL_KEY,
            has_mappings=has_mappings,
            mappings=";".join([v["name"] for v in mappings]),
            has_no_gap_filled_background_emissions=has_no_gap_filled_background_emissions,
            input_value=input_value,
            **extra_logs
        )

        should_run = all(
            [has_mappings, has_no_gap_filled_background_emissions, input_value]
        )
        logShouldRun(
            cycle,
            model,
            input_term_id,
            should_run,
            methodTier=TIER,
            model_key=MODEL_KEY,
            **extra_logs
        )

        results = (
            process_input_mappings(
                cycle,
                input,
                mappings,
                TermTermType.EMISSION,
                lookup_values,
                **(extra_logs | {"model": model, "model_key": MODEL_KEY})
            )
            if should_run
            else {}
        )
        has_no_gap_filled_background_emissions and log_missing_emissions_func(
            input_term_id,
            list(map(parse_term_id, results.keys())),
            **(extra_logs | {"has_mappings": has_mappings})
        )
        return non_empty_list(
            [
                _emission(
                    model=model,
                    term_id=parse_term_id(term_id),
                    value=sum([v["value"] * v["coefficient"] for v in values])
                    * input_value,
                    input=input,
                    country_id=values[0].get("country"),
                    key_id=values[0].get("key"),
                    cutoff_value_func=cutoff_value_func,
                )
                for term_id, values in results.items()
            ]
        )

    return run


def run(
    model: str,
    cycle: dict,
    lookup_mapping_key: str,
    lookup_values: LookupValuesType,
    filter_term_types: Optional[Union[TermTermType, List[TermTermType]]] = [],
    filter_by_country: bool = False,
    cutoff_value_func: CutoffValueFunc = None,
    cutoff_percentage=None,
):
    extra_inputs = (
        get_pesticides_from_inputs(cycle, include_pesticideAI=False)
        if not filter_term_types or TermTermType.PESTICIDEAI.value in filter_term_types
        else []
    ) + (
        get_fertilisers_from_inputs(cycle)
        if not filter_term_types
        or TermTermType.INORGANICFERTILISER.value in filter_term_types
        else []
    )
    inputs = get_background_inputs(
        cycle, extra_inputs=extra_inputs, filter_term_types=filter_term_types
    )
    grouped_inputs = group_by_keys(inputs, ["term", "operation", "animal", "country"])
    emissions = flatten(
        map(
            _run_input(
                model,
                cycle,
                lookup_mapping_key,
                lookup_values,
                filter_by_country,
                cutoff_value_func,
            ),
            grouped_inputs.values(),
        )
    )
    emissions = (
        emissions
        if cutoff_value_func is None
        else filter_blank_nodes_cutoff(emissions, cutoff_percentage)
    )
    # group the emissions again to make sure we do not return duplicated emissions
    grouped_emissions = group_by_keys(emissions, _UNIQUE_FIELDS)
    return [
        emissions[0] | {"value": [list_sum(flatten([v["value"] for v in emissions]))]}
        for emissions in grouped_emissions.values()
    ]
