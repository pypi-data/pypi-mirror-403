from functools import reduce
from hestia_earth.schema import TermTermType
from hestia_earth.utils.model import (
    find_term_match,
    filter_list_term_type,
    find_primary_product,
)
from hestia_earth.utils.tools import (
    non_empty_list,
    list_average,
    list_sum,
    safe_parse_float,
)
from hestia_earth.utils.lookup import extract_grouped_data

from hestia_earth.models.log import logShouldRun, logRequirements, log_as_table
from hestia_earth.models.utils.term import get_lookup_value
from . import MODEL


def run_products_average(cycle: dict, term_id: str, get_value_func):
    products = cycle.get("products", [])

    values_by_product = [
        (p.get("term", {}).get("@id"), get_value_func(p)) for p in products
    ]
    values = non_empty_list([value for term_id, value in values_by_product])
    has_values = len(values) > 0

    logRequirements(
        cycle,
        model=MODEL,
        term=term_id,
        has_values=has_values,
        details=log_as_table(
            [{"id": term_id, "value": value} for term_id, value in values_by_product]
        ),
    )

    should_run = all([has_values])
    logShouldRun(cycle, MODEL, term_id, should_run)
    return list_average(values) if should_run else None


def _excreta_product_id(data: str, term_id: str, return_single_value: bool = False):
    value = extract_grouped_data(data, term_id) or ""
    values = non_empty_list(value.split("|"))
    return values[0] if return_single_value and values else values


def get_excreta_product_with_ratio(cycle: dict, lookup: str, **log_args):
    product = find_primary_product(cycle) or {}

    data = get_lookup_value(product.get("term"), lookup, model=MODEL, **log_args)
    data_percentage = get_lookup_value(
        product.get("term"), lookup + "-percentage", skip_debug=True
    )

    default_product_ids = _excreta_product_id(data, "default")
    default_product_id = default_product_ids[0] if default_product_ids else None
    default_product_ratios = {
        product_id: safe_parse_float(
            extract_grouped_data(data_percentage, product_id), default=1
        )
        for product_id in default_product_ids
    }

    # find matching practices and assign a ratio for each
    practices = filter_list_term_type(cycle.get("practices", []), TermTermType.SYSTEM)
    values = [
        {
            "id": practice.get("term", {}).get("@id"),
            "product-id": _excreta_product_id(
                data, practice.get("term", {}).get("@id"), return_single_value=True
            )
            or default_product_id,
            "value": list_sum(practice.get("value")),
        }
        for practice in practices
        # only keep practices with positive value
        if list_sum(practice.get("value", [-1]), 0) > 0
    ]
    # if no matches, use default ids with ratios
    valid_values = (
        values
        if values and any([v["product-id"] != default_product_id for v in values])
        else [
            {"product-id": product_id, "value": default_product_ratios.get(product_id)}
            for product_id in default_product_ids
        ]
    )

    logRequirements(
        cycle,
        model=MODEL,
        **log_args,
        values=log_as_table(valid_values),
        default_product_ids=";".join(default_product_ids)
    )

    total_value = list_sum([p.get("value") for p in valid_values])

    # group values by product id
    grouped_values = reduce(
        lambda p, c: p | {c["product-id"]: p.get(c["product-id"], []) + [c]},
        valid_values,
        {},
    )
    # calculate ratio for each product
    grouped_values = [
        v[0]
        | {"ratio": round(list_sum([v.get("value") for v in v]) * 100 / total_value, 2)}
        for v in grouped_values.values()
    ]

    values_with_products = [
        (find_term_match(cycle.get("products", []), p.get("product-id")), p)
        for p in grouped_values
    ]
    products = (
        [
            (
                product
                or {
                    "@type": "Product",
                    "term": {"@type": "Term", "@id": v.get("product-id")},
                }
            )
            | {"value": [v.get("ratio")]}
            for product, v in values_with_products
            # ignore matching products with an existing value
            if all(
                [
                    not product or not product.get("value", []),
                    product or v.get("product-id"),
                ]
            )
        ]
        if values_with_products
        else None
    )

    return products or non_empty_list(
        [
            {
                "@type": "Product",
                "term": {"@type": "Term", "@id": product_id},
                "value": [round(100 / len(default_product_ids), 2)],
            }
            for product_id in default_product_ids
        ]
    )
