from hestia_earth.schema import CycleStartDateDefinition
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.model import find_primary_product, find_term_match
from hestia_earth.utils.date import YEAR

from hestia_earth.models.log import (
    format_bool,
    format_float,
    format_func_name,
    format_str,
    logRequirements,
    logShouldRun,
)
from hestia_earth.models.utils import select_run_func, sum_is_100, weighted_average
from hestia_earth.models.utils.practice import _new_practice
from hestia_earth.models.utils.crop import is_plantation
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "or": [
            {
                "@doc": "if startDateDefinition is `harvest of previous crop`, cycleDuration is required",
                "cycleDuration": "> 0",
                "startDateDefinition": "harvest of previous crop",
            },
            {
                "@doc": "if startDateDefinition is `soil preparation date`, `sowing date` or `transplanting date`, further cycleDuration and cycleDuration are required",  # noqa: E501
                "startDateDefinition": [
                    "soil preparation date",
                    "sowing date",
                    "transplanting date",
                ],
                "cycleDuration": "> 0",
                "practices": [
                    {
                        "@type": "Practice",
                        "term.@id": "cycleDuration",
                        "value": "",
                    }
                ],
            },
            {
                "@doc": "if startDateDefinition is `one year prior` the model can run without further data",
                "startDateDefinition": "one year prior",
            },
            {
                "@doc": "else, for any startDateDefinition the user can specify the area of their site under singleCropped, doubleCropped and tripleCropped regimes",  # noqa: E501
                "practices": [
                    {
                        "@type": "Practice",
                        "term.@id": "singleCropped",
                        "value": "",
                    },
                    {
                        "@type": "Practice",
                        "term.@id": "doubleCropped",
                        "value": "",
                    },
                    {
                        "@type": "Practice",
                        "term.@id": "tripleCropped",
                        "value": "",
                    },
                ],
            },
        ],
    }
}
RETURNS = {"Practice": [{"value": ""}]}
LOOKUPS = {"crop": "isPlantation"}
TERM_ID = "croppingIntensity"

_SHORT_FALLOW_DURATION_TERM_ID = "shortFallowDuration"
_SINGLE_CROPPED_TERM_ID = "singleCropped"
_DOUBLE_CROPPED_TERM_ID = "doubleCropped"
_TRIPLE_CROPPED_TERM_ID = "tripleCropped"

_YEAR = round(YEAR)

_SINGLE_CROPPED_CI = 1
_DOUBLE_CROPPED_CI = 1 / 2
_TRIPLE_CROPPED_CI = 1 / 3


def _run_with_cycleDuration(cycle_duration: float):
    """
    In cases where `cycle.cycleDuration` includes both the cropping duration and short fallow duration:

    ```
    croppingIntensity = cycle.cycleDuration / 365.
    ```

    Parameters
    ----------
    cycle_duration : float
        The Cycle's duration, including short fallow, days.

    Returns
    -------
    list[dict]
        A list of HESTIA [Practice](https://www.hestia.earth/schema/Practice) nodes with `term.termType` =
        `croppingIntensity`
    """
    value = cycle_duration / _YEAR
    return [_new_practice(term=TERM_ID, model=MODEL, value=value)]


def _run_with_cycleDuration_shortFallowDuration(
    cycle_duration: float, short_fallow_duration: float
):
    """
    In cases where `cycle.cycleDuration` includes the cropping duration, but excludes the short fallow duration:

    ```
    croppingIntensity = (cycle.cycleDuration + shortFallowDuration) / 365.
    ```

    Parameters
    ----------
    cycle_duration : float
        The Cycle's duration, excluding short fallow, days.
    short_fallow_duration : float
        The value of the Cycle's `shortFallowDuration` Practice node, days.

    Returns
    -------
    list[dict]
        A list of HESTIA [Practice](https://www.hestia.earth/schema/Practice) nodes with `term.termType` =
        `croppingIntensity`
    """
    duration = cycle_duration + short_fallow_duration
    value = duration / _YEAR
    return [_new_practice(term=TERM_ID, model=MODEL, value=value)]


def _run_with_one_year_prior():
    """Duration equals one year."""
    return [_new_practice(term=TERM_ID, model=MODEL, value=1)]


def _calc_with_multicropping(
    single_cropped: float, double_cropped: float, triple_cropped: float
) -> float:
    """
    Calculate the average cropping intensity via a weighted average of multicropping term values.
    """
    return weighted_average(
        [
            (_SINGLE_CROPPED_CI, single_cropped),
            (_DOUBLE_CROPPED_CI, double_cropped),
            (_TRIPLE_CROPPED_CI, triple_cropped),
        ]
    )


def _run_with_multicropping(
    single_cropped: float,
    double_cropped: float,
    triple_cropped: float,
):
    """
    In cases where `cycle.cycleDuration` is not available, cropping intensity can be estimated using multicropping
    Practices: `singleCropped`, `doubleCropped`, and `tripleCropped`.

    Parameters
    ----------
    single_cropped : float
        The area of land under a single cropping regime, % area.
    double_cropped : float
        The area of land under a double cropping regime, % area.
    triple_cropped : float
        The area of land under a triple cropping regime, % area.

    Returns
    -------
    list[dict]
        A list of HESTIA [Practice](https://www.hestia.earth/schema/Practice) nodes with `term.termType` =
        `croppingIntensity`
    """
    value = _calc_with_multicropping(single_cropped, double_cropped, triple_cropped)
    return [_new_practice(term=TERM_ID, model=MODEL, value=value)]


def _should_run_with_cycleDuration(
    *,
    is_plantation: bool,
    start_date_definition: str,
    cycle_duration: float,
    **_,
):
    """
    Determine whether it is possible to calculate `croppingIntensity` using `cycle.cycleDuration`.

    Keyword Arguments
    -----------------
    is_plantation : bool
        Whether the primary product is considered a plantation crop.
    start_date_definition : str
        The Cycle's `startDateDefinition`.
    cycle_duration : float
        The Cycle's duration, days.

    Returns
    -------
    should_run : bool
    cycle_duration : float
    """
    should_run = all(
        [
            not is_plantation,
            cycle_duration,
            start_date_definition
            == CycleStartDateDefinition.HARVEST_OF_PREVIOUS_CROP.value,
        ]
    )

    return should_run, cycle_duration


def _should_run_with_cycleDuration_shortFallowDuration(
    *,
    is_plantation: bool,
    start_date_definition: str,
    cycle_duration: float,
    short_fallow_duration: float,
    **_,
):
    """
    Determine whether it is possible to calculate `croppingIntensity` using `cycle.cycleDuration` and
    `shortFallowDuration`.

    Keyword Arguments
    -----------------
    is_plantation : bool
        Whether the primary product is considered a plantation crop.
    start_date_definition : str
        The Cycle's `startDateDefinition`.
    cycle_duration : float
        The Cycle's duration, days.
    short_fallow_duration : float
        The value of the Cycle's `shortFallowDuration` Practice node, days.

    Returns
    -------
    should_run : bool
    cycle_duration : float
    short_fallow_duration : float
    """
    should_run = all(
        [
            not is_plantation,
            cycle_duration,
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
    is_plantation: bool,
    start_date_definition: str,
    **_,
):
    """
    Determine whether it is possible to calculate `croppingIntensity` using `cycle.startDateDefinition` ==
    `one year prior`.
    """
    should_run = all(
        [
            not is_plantation,
            start_date_definition == CycleStartDateDefinition.ONE_YEAR_PRIOR.value,
        ]
    )
    return (should_run,)


def _should_run_with_multicropping(
    *,
    is_plantation: bool,
    single_cropped: float,
    double_cropped: float,
    triple_cropped: float,
    **_,
):
    """
    Determine whether it is possible to calculate `croppingIntensity` using `singleCropped`, `doubleCropped` and
    `tripleCropped` Practices.

    Keyword Arguments
    -----------------
    is_plantation : bool
        Whether the primary product is considered a plantation crop.
    single_cropped : float
        The area of land under a single cropping regime, % area.
    double_cropped : float
        The area of land under a double cropping regime, % area.
    triple_cropped : float
        The area of land under a triple cropping regime, % area.

    Returns
    -------
    should_run : bool
    single_cropped : float
    double_cropped : float
    triple_cropped : float
    """

    is_multicropping_data_complete = sum_is_100(
        single_cropped, double_cropped, triple_cropped
    )

    should_run = all([not is_plantation, is_multicropping_data_complete])
    return should_run, single_cropped, double_cropped, triple_cropped


CALC_STRATEGIES = {
    _should_run_with_cycleDuration: _run_with_cycleDuration,
    _should_run_with_cycleDuration_shortFallowDuration: _run_with_cycleDuration_shortFallowDuration,
    _should_run_with_one_year_prior: _run_with_one_year_prior,
    _should_run_with_multicropping: _run_with_multicropping,
}
"""
A mapping between `_should_run` and `_run` functions for each run strategy.
"""


def _should_run(cycle: dict):
    """
    Extract data from Cycle node and determine whether the model should run.
    """
    practices = cycle.get("practices", [])

    product = find_primary_product(cycle) or {}
    product_term = (product or {}).get("term", {})
    is_plantation_ = is_plantation(MODEL, TERM_ID, product_term.get("@id"))

    cycle_duration = cycle.get("cycleDuration")
    start_date_definition = cycle.get("startDateDefinition")

    short_fallow_duration = get_node_value(
        find_term_match(practices, _SHORT_FALLOW_DURATION_TERM_ID), default=None
    )

    single_cropped = get_node_value(find_term_match(practices, _SINGLE_CROPPED_TERM_ID))
    double_cropped = get_node_value(find_term_match(practices, _DOUBLE_CROPPED_TERM_ID))
    triple_cropped = get_node_value(find_term_match(practices, _TRIPLE_CROPPED_TERM_ID))

    run_func, *args = select_run_func(
        CALC_STRATEGIES,
        is_plantation=is_plantation_,
        start_date_definition=start_date_definition,
        cycle_duration=cycle_duration,
        short_fallow_duration=short_fallow_duration,
        single_cropped=single_cropped,
        double_cropped=double_cropped,
        triple_cropped=triple_cropped,
    )

    should_run = all([run_func is not None])

    logRequirements(
        cycle,
        model=MODEL,
        term=TERM_ID,
        is_plantation=format_bool(is_plantation_),
        start_date_definition=format_str(start_date_definition),
        cycle_duration=format_float(cycle_duration, "days"),
        short_fallow_duration=format_float(short_fallow_duration, "days"),
        single_cropped=format_float(single_cropped, "pct area"),
        double_cropped=format_float(double_cropped, "pct area"),
        triple_cropped=format_float(triple_cropped, "pct area"),
        run_strategy=format_func_name(run_func),
    )

    logShouldRun(cycle, MODEL, TERM_ID, should_run)
    return should_run, run_func, *args


def run(cycle: dict):
    """
    Run the model on a Cycle.
    """
    should_run, run_func, *args = _should_run(cycle)
    return run_func(*args) if should_run else []
