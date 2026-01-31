from functools import reduce, lru_cache
from typing import Callable, Union, List, Optional, Tuple, TypeAlias
from hestia_earth.schema import TermTermType, EmissionMethodTier
from hestia_earth.utils.lookup import download_lookup, is_missing_value, lookup_columns
from hestia_earth.utils.model import find_term_match, filter_list_term_type
from hestia_earth.utils.tools import flatten, non_empty_list, safe_parse_float, omit
from hestia_earth.utils.emission import cycle_emissions_in_system_boundary
from hestia_earth.utils.blank_node import group_by_keys

from hestia_earth.models.log import logShouldRun, logRequirements, debugValues
from . import is_from_model
from .constant import DEFAULT_COUNTRY_ID
from .term import get_lookup_value
from .region import get_parent_regions

LookupValuesFunc: TypeAlias = Callable[[str], dict]
LookupValuesType: TypeAlias = Union[Tuple[LookupValuesFunc, None], Tuple[str, str]]
CutoffValueFunc: TypeAlias = Callable[[str], float]


def _parse_mapping(mapping: str, total_mappings: int):
    parts = mapping.split(":")
    # 3 parts means country:mapping:value
    # 2 parts can be country:mapping or mapping:value
    return (
        {"country": parts[0], "name": parts[1], "coeff": safe_parse_float(parts[2])}
        if len(parts) == 3
        else (
            {"country": parts[0], "name": parts[1], "coeff": 1 / total_mappings}
            if safe_parse_float(parts[1], default=None) is None
            else {"name": parts[0], "coeff": safe_parse_float(parts[1])}
        )
    )


def _filter_mappings_by_country(country: dict, mappings: List[dict]):
    processes = group_by_keys(mappings, ["country"])
    country_ids = processes.keys()
    input_country = country.get("@id")

    preferred_mapping_country = (
        [
            input_country,
            (
                next(
                    (c for c in get_parent_regions(input_country) if c in country_ids),
                    None,
                )
                if (
                    input_country
                    and input_country not in country_ids
                    and input_country != DEFAULT_COUNTRY_ID
                )
                else None
            ),
            DEFAULT_COUNTRY_ID,
            "default",
        ]
        if mappings
        else []
    )

    return (
        next(
            (
                processes.get(k)
                for k in preferred_mapping_country
                if k is not None and k in processes
            ),
            [],
        )
        if mappings
        else []
    )


def get_input_mappings(
    model: str, input: dict, lookup_col: str, filter_by_country: bool = False
):
    term = input.get("term", {})
    term_id = term.get("@id")
    value = get_lookup_value(term, lookup_col, model=model, term=term_id)
    mappings = non_empty_list(value.split(";")) if value else []
    mappings = [_parse_mapping(m, len(mappings)) for m in mappings]
    return (
        _filter_mappings_by_country(input.get("country", {}), mappings)
        if filter_by_country
        else mappings
    )


def _animal_inputs(animal: dict):
    inputs = animal.get("inputs", [])
    return [
        (input | {"animalId": animal["animalId"], "animal": animal.get("term", {})})
        for input in inputs
    ]


def _should_run_input(
    products: list, filter_term_types: Union[TermTermType, List[TermTermType]]
):
    term_types = (
        [t for t in filter_term_types]
        if isinstance(filter_term_types, list)
        else [filter_term_types]
    )
    term_types = [(t if isinstance(t, str) else t.value) for t in term_types]

    def should_run(input: dict):
        return all(
            [
                not term_types or input.get("term", {}).get("termType") in term_types,
                # make sure Input is not a Product as well or we might double-count emissions
                find_term_match(products, input.get("term", {}).get("@id"), None)
                is None,
                # ignore inputs which are flagged as Product of the Cycle
                not input.get("fromCycle", False),
                not input.get("producedInCycle", False),
            ]
        )

    return should_run


def get_background_inputs(
    cycle: dict,
    extra_inputs: list = [],
    filter_term_types: Optional[Union[TermTermType, List[TermTermType]]] = [],
) -> List[dict]:
    # add all the properties of some Term that include others with the mapping
    inputs = flatten(
        cycle.get("inputs", [])
        + list(map(_animal_inputs, cycle.get("animals", [])))
        + extra_inputs
    )
    return list(
        filter(_should_run_input(cycle.get("products", []), filter_term_types), inputs)
    )


def no_gap_filled_background_emissions(
    node: dict,
    list_key: str = "emissions",
    term_type: TermTermType = TermTermType.EMISSION,
):
    blank_nodes = filter_list_term_type(node.get(list_key, []), term_type)

    def check_input(input: dict):
        input_term_id = input.get("term", {}).get("@id")
        operation_term_id = input.get("operation", {}).get("@id")
        animal_term_id = input.get("animal", {}).get("@id")

        return not any(
            [
                is_from_model(blank_node)
                for blank_node in blank_nodes
                if all(
                    [
                        any(
                            [
                                i.get("@id") == input_term_id
                                for i in blank_node.get("inputs", [])
                            ]
                        ),
                        blank_node.get("operation", {}).get("@id") == operation_term_id,
                        blank_node.get("animal", {}).get("@id") == animal_term_id,
                    ]
                )
            ]
        )

    return check_input


def _all_background_emission_term_ids(node: dict, termType: TermTermType):
    term_ids = cycle_emissions_in_system_boundary(node, termType=termType)
    background_ids = list(
        set(
            [
                get_lookup_value(
                    {"termType": termType.value, "@id": term_id},
                    "inputProductionGroupId",
                )
                for term_id in term_ids
            ]
        )
    )
    # make sure input production emission is itself in the system boundary
    return [term_id for term_id in background_ids if term_id in term_ids]


def log_missing_emissions(
    node: dict, termType: TermTermType = TermTermType.EMISSION, **log_args
):
    all_emission_term_ids = _all_background_emission_term_ids(node, termType)

    def log_input(
        input_term_id: str, included_emission_term_ids: list, **extra_log_args
    ):
        missing_emission_term_ids = non_empty_list(
            [
                term_id
                for term_id in all_emission_term_ids
                if term_id not in included_emission_term_ids
            ]
        )

        for emission_id in missing_emission_term_ids:
            # debug value on the emission itself so it appears for the input
            debugValues(
                node,
                term=emission_id,
                value=None,
                coefficient=None,
                input=input_term_id,
                **log_args,
                **extra_log_args,
            )
            logRequirements(
                node,
                term=input_term_id,
                emission_id=emission_id,
                has_emission_factor=False,
                **log_args,
                **extra_log_args,
            )
            logShouldRun(
                node,
                term=input_term_id,
                should_run=False,
                emission_id=emission_id,
                **log_args,
                **extra_log_args,
            )

    return log_input


_KEY_TO_FIELD = {"inputs": "key"}


def _key_to_field(key: str):
    return _KEY_TO_FIELD.get(key) or key


def _values_from_column(index_column: str, column: str, value: str):
    values = column.split("+")
    term_id = values[0]
    value = safe_parse_float(value, default=None)
    return (
        {"term_id": term_id, "value": value}
        | {_key_to_field(v.split("[")[0]): v.split("[")[1][:-1] for v in values[1:]}
        if all(
            [
                column != index_column,
                not column.startswith("ecoinvent"),
                not column.startswith("ecoalim"),
                not column.startswith("bafu"),
                not is_missing_value(value),
            ]
        )
        else None
    )


def convert_background_lookup(lookup, index_column: str):
    columns = lookup_columns(lookup)
    indexed_df = lookup.set_index(index_column, drop=False).copy()
    return {
        index_key: non_empty_list(
            [
                _values_from_column(index_column, column, row_data[column])
                for column in columns
            ]
        )
        for index_key, row_data in indexed_df.to_dict("index").items()
    }


def parse_term_id(term_id: str):
    return term_id.split("-")[0]


def _join_term_id(data: dict):
    return "-".join(non_empty_list(list(omit(data, ["value"]).values())))


@lru_cache()
def _build_mappings_lookup(
    lookup_name_prefix: str, lookup_index_key: str, term_type: str
):
    lookup = download_lookup(
        f"{lookup_name_prefix}{term_type}.csv", keep_in_memory=False
    )
    return convert_background_lookup(lookup=lookup, index_column=lookup_index_key)


def _process_mapping(
    node: dict,
    input: dict,
    term_type: TermTermType,
    lookup_values: LookupValuesType,
    **log_args,
) -> dict:
    input_term_id = input.get("term", {}).get("@id")
    operation_term_id = input.get("operation", {}).get("@id")
    animal_term_id = input.get("animal", {}).get("@id")

    def _default_mapping_func(term_type: str):
        lookup_name_prefix, lookup_index_key = lookup_values
        return _build_mappings_lookup(lookup_name_prefix, lookup_index_key, term_type)

    def add(prev: dict, mapping: dict):
        mapping_func = (
            lookup_values[0] if callable(lookup_values[0]) else _default_mapping_func
        )
        data = mapping_func(term_type.value)
        values = data.get(mapping["name"], {})
        coefficient = mapping["coeff"]
        for data in values:
            term_id = data.get("term_id")

            # log run on each node so we know it did run
            logShouldRun(
                node,
                term=input_term_id,
                should_run=True,
                methodTier=EmissionMethodTier.BACKGROUND.value,
                emission_id=term_id,
                **log_args,
            )
            debugValues(
                node,
                term=term_id,
                value=data.get("value"),
                coefficient=coefficient,
                input=input_term_id,
                operation=operation_term_id,
                animal=animal_term_id,
                **log_args,
            )
            group_id = _join_term_id(data)
            prev[group_id] = prev.get(group_id, []) + [
                omit(data, ["term_id"]) | {"coefficient": coefficient}
            ]
        return prev

    return add


def process_input_mappings(
    node: dict,
    input: dict,
    mappings: list,
    term_type: TermTermType,
    lookup_values: LookupValuesType,
    **log_args,
):
    return reduce(
        _process_mapping(node, input, term_type, lookup_values, **log_args),
        mappings,
        {},
    )


CUTOFF_KEY = "cutoff_coeff"


def cutoff_id(term_id: str, country_id: str = None, key_id: str = None):
    return (
        term_id
        + (f"+inputs[{key_id}]" if key_id else "")
        + (f"+country[{country_id}]" if country_id else "")
    )


def filter_blank_nodes_cutoff(blank_nodes: list, max_percentage: float):
    # use the generic contibution of the blank node towards EF Score to remove the lowest percentage
    total_contributions = sum([v.get(CUTOFF_KEY, 0) for v in blank_nodes])
    blank_nodes_with_contributions = sorted(
        [(v, v.get(CUTOFF_KEY, 0) * 100 / total_contributions) for v in blank_nodes],
        key=lambda v: v[1],
        reverse=True,
    )

    sum_contributions = 0
    filtered_blank_nodes = []
    for blank_node, contribution in blank_nodes_with_contributions:
        sum_contributions = sum_contributions + contribution
        if sum_contributions > max_percentage:
            break
        filtered_blank_nodes.append(omit(blank_node, [CUTOFF_KEY]))

    return filtered_blank_nodes
