from hestia_earth.schema import TermTermType, CycleStartDateDefinition
from hestia_earth.utils.model import find_primary_product, find_term_match
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.date import YEAR
from hestia_earth.utils.tools import to_precision

from hestia_earth.models.log import format_func_name, logRequirements, logShouldRun
from hestia_earth.models.utils import select_run_func
from hestia_earth.models.utils.crop import is_permanent_crop
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "cycleDuration": "> 0",
        "none": {"otherSites": [{"@type": "Site"}]},
        "startDateDefinition": "",
        "optional": {
            "@doc": "if the primary product is a temporary crop, additional properties are required",
            "products": [
                {"@type": "Product", "primary": "True", "term.termType": "crop"}
            ],
            "or": [
                {
                    "@doc": "if startDateDefinition is `harvest of previous crop`, no further properties are required",  # noqa: E501
                    "startDateDefinition": "harvest of previous crop",
                },
                {
                    "@doc": "if startDateDefinition is `soil preparation date`, `sowing date` or `transplanting date`, further properties are required",  # noqa: E501
                    "startDateDefinition": [
                        "soil preparation date",
                        "sowing date",
                        "transplanting date",
                    ],
                    "practices": [
                        {
                            "@type": "Practice",
                            "term.@id": "shortFallowDuration",
                            "value": "",
                        }
                    ],
                },
                {
                    "@doc": "else, siteDuration can be calculated from `croppingIntensity",
                    "practices": [
                        {
                            "@type": "Practice",
                            "value": "",
                            "term.@id": "croppingIntensity",
                        },
                    ],
                },
            ],
        },
    }
}
LOOKUPS = {"crop": "cropGroupingFAO"}
RETURNS = {"the duration as a `number`": ""}
MODEL_KEY = "siteDuration"

_YEAR = round(YEAR)

_SHORT_FALLOW_DURATION_TERM_ID = "shortFallowDuration"
_CROPPING_INTENSITY_TERM_ID = "croppingIntensity"


def _run_with_cycleDuration(cycle_duration: float):
    """
    In cases where `cycle.cycleDuration` includes both the cropping duration and short fallow duration,
    `cycle.siteDuration` = `cycle.cycleDuration`.

    Parameters
    ----------
    cycle_duration : float
        The Cycle's duration, including short fallow, days.

    Returns
    -------
    float
        The duration that a Cycle occupies it's Site, days.
    """
    return to_precision(cycle_duration)


def _run_with_cycleDuration_shortFallowDuration(
    cycle_duration: float, short_fallow_duration: float
):
    """
    In cases where `cycle.cycleDuration` includes the cropping duration, but excludes the short fallow duration,
    `cycle.siteDuration` = `cycle.cycleDuration` + `shortFallowDuration`.

    Parameters
    ----------
    cycle_duration : float
        The Cycle's duration, including short fallow, days.
    short_fallow_duration : float
        The value of the Cycle's `shortFallowDuration` Practice node, days.

    Returns
    -------
    float
        The duration that a Cycle occupies it's Site, days.
    """
    return to_precision(cycle_duration + short_fallow_duration)


def _run_with_one_year_prior():
    """Site occupied for one year, regardless of cycle duration."""
    return _YEAR


def _run_with_croppingIntensity(cropping_intensity: float):
    """Site occupied for `365 * cropping_intensity`."""
    return to_precision(_YEAR * cropping_intensity)


def _should_run_with_cycleDuration(
    *,
    cycle_duration,
    has_single_site,
    is_primary_crop_product,
    is_permanent_crop,
    start_date_definition,
    **_,
):
    """
    Determine whether it is possible to calculate `cycle.siteDuration` using `cycle.cycleDuration`.
    """
    should_run = all(
        [
            cycle_duration > 0,
            has_single_site,
            any(
                [
                    not is_primary_crop_product,
                    is_permanent_crop,
                    start_date_definition
                    == CycleStartDateDefinition.HARVEST_OF_PREVIOUS_CROP.value,
                ]
            ),
        ]
    )
    return should_run, cycle_duration


def _should_run_with_cycleDuration_shortFallowDuration(
    *,
    cycle_duration,
    has_single_site,
    is_primary_crop_product,
    is_permanent_crop,
    short_fallow_duration,
    start_date_definition,
    **_,
):
    """
    Determine whether it is possible to calculate `cycle.siteDuration` using `cycle.cycleDuration` and
    `shortFallowDuration`.
    """
    should_run = all(
        [
            cycle_duration > 0,
            has_single_site,
            is_primary_crop_product,
            not is_permanent_crop,
            short_fallow_duration is not None,
            start_date_definition
            in [
                CycleStartDateDefinition.SOIL_PREPARATION_DATE.value,
                CycleStartDateDefinition.SOWING_DATE.value,
                CycleStartDateDefinition.TRANSPLANTING_DATE.value,
            ],
        ]
    )
    return should_run, cycle_duration, short_fallow_duration


def _should_run_with_one_year_prior(
    *,
    has_single_site,
    start_date_definition,
    **_,
):
    """
    Determine whether it is possible to calculate `cycle.siteDuration` using `cycle.startDateDefinition` ==
    `one year prior`.
    """
    should_run = all(
        [
            has_single_site,
            start_date_definition == CycleStartDateDefinition.ONE_YEAR_PRIOR.value,
        ]
    )
    return (should_run,)


def _should_run_with_croppingIntensity(
    *,
    cropping_intensity,
    has_single_site,
    is_primary_crop_product,
    is_permanent_crop,
    **_,
):
    should_run = all(
        [
            cropping_intensity and cropping_intensity > 0,
            has_single_site,
            is_primary_crop_product,
            not is_permanent_crop,
        ]
    )
    return should_run, cropping_intensity


CALC_STRATEGIES = {
    _should_run_with_cycleDuration: _run_with_cycleDuration,
    _should_run_with_cycleDuration_shortFallowDuration: _run_with_cycleDuration_shortFallowDuration,
    _should_run_with_one_year_prior: _run_with_one_year_prior,
    _should_run_with_croppingIntensity: _run_with_croppingIntensity,
}
"""
A mapping between `_should_run` and `_run` functions for each run strategy.
"""


def _should_run(cycle: dict):
    """
    Extract data from the input Cycle node and determine whether there is suitable data for the model to run.

    Depending on `cycle.startDateDefinition`, different strategies should be used to calculate `cycle.siteDuration`.

    Parameters
    ----------
    cycle : dict
        The Cycle node on which the model should run.

    Returns
    ------
    should_run : bool
        Whether or not the model should run.
    run_func : Callable
        A run function to calculate `cycle.siteDuration` with signature `(*args) -> float`.
    cycle_duration : float
        The Cycle's duration, including short fallow, days.
    short_fallow_duration : float
        The value of the Cycle's `shortFallowDuration` Practice node, days.
    """
    cycle_duration = cycle.get("cycleDuration", 0)
    has_single_site = len(cycle.get("otherSites", [])) == 0
    start_date_definition = cycle.get("startDateDefinition")

    product = find_primary_product(cycle)
    product_term = (product or {}).get("term", {})
    is_primary_crop_product = product_term.get("termType") == TermTermType.CROP.value
    is_permanent_crop_ = is_permanent_crop(MODEL, MODEL_KEY, product_term)

    short_fallow_duration = get_node_value(
        find_term_match(cycle.get("practices", []), _SHORT_FALLOW_DURATION_TERM_ID),
        default=None,
    )
    cropping_intensity = get_node_value(
        find_term_match(cycle.get("practices", []), _CROPPING_INTENSITY_TERM_ID),
        default=None,
    )

    run_func, *args = select_run_func(
        CALC_STRATEGIES,
        cropping_intensity=cropping_intensity,
        cycle_duration=cycle_duration,
        has_single_site=has_single_site,
        is_primary_crop_product=is_primary_crop_product,
        is_permanent_crop=is_permanent_crop_,
        short_fallow_duration=short_fallow_duration,
        start_date_definition=start_date_definition,
    )

    should_run = all([run_func is not None])

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        cropping_intensity=cropping_intensity,
        cycle_duration=cycle_duration,
        has_single_site=has_single_site,
        is_primary_crop_product=is_primary_crop_product,
        is_permanent_crop=is_permanent_crop_,
        short_fallow_duration=short_fallow_duration,
        start_date_definition=start_date_definition,
        run_strategy=format_func_name(run_func),
    )

    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY)

    return should_run, run_func, *args


def run(cycle: dict):
    """
    Run the model on a Cycle.
    """
    should_run, run_func, *args = _should_run(cycle)
    return run_func(*args) if should_run else None
