from hestia_earth.schema import CycleStartDateDefinition, TermTermType
from hestia_earth.utils.blank_node import get_node_value
from hestia_earth.utils.model import find_term_match, find_primary_product
from hestia_earth.utils.date import (
    DatestrFormat,
    diff_in,
    parse_gapfilled_datestr,
    TimeUnit,
    validate_datestr_format,
    YEAR,
)
from hestia_earth.utils.tools import to_precision

from hestia_earth.models.log import (
    format_bool,
    format_conditional_message,
    format_float,
    format_str,
    logRequirements,
    logShouldRun,
)
from hestia_earth.models.utils import select_run_func, sum_is_100, weighted_average
from hestia_earth.models.utils.crop import is_permanent_crop
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "endDate": "",
        "optional": {
            "startDate": "",
            "startDateDefinition": "",
            "products": [
                {"@type": "Product", "primary": "True", "term.termType": "crop"}
            ],
            "practices": [
                {"@type": "Practice", "value": "", "term.@id": "croppingIntensity"},
                {"@type": "Practice", "value": "", "term.@id": "shortFallowDuration"},
                {"@type": "Practice", "value": "", "term.@id": "singleCropped"},
                {"@type": "Practice", "value": "", "term.@id": "doubleCropped"},
                {"@type": "Practice", "value": "", "term.@id": "tripleCropped"},
            ],
        },
    }
}
RETURNS = {"a `number` or `None` if requirements are not met": ""}
LOOKUPS = {"crop": "cropGroupingFAO"}
MODEL_KEY = "cycleDuration"

_CROPPING_INTENSITY_TERM_ID = "croppingIntensity"
_SHORT_FALLOW_DURATION_TERM_ID = "shortFallowDuration"
_SINGLE_CROPPED_TERM_ID = "singleCropped"
_DOUBLE_CROPPED_TERM_ID = "doubleCropped"
_TRIPLE_CROPPED_TERM_ID = "tripleCropped"

_YEAR = round(YEAR)

_SINGLE_CROPPED_DURATION = _YEAR
_DOUBLE_CROPPED_DURATION = _YEAR / 2
_TRIPLE_CROPPED_DURATION = _YEAR / 3

_START_DATE_DEFINITIONS_EXCLUDE_SHORT_FALLOW_DURATION = (
    CycleStartDateDefinition.SOIL_PREPARATION_DATE.value,
    CycleStartDateDefinition.SOWING_DATE.value,
    CycleStartDateDefinition.TRANSPLANTING_DATE.value,
)

_PERMANENT_RATIO = 1
_DEFAULT_TEMPORARY_RATIO = 1


def _run_with_startDate_endDate(start_date: str, end_date: str):
    """
    In cases where `startDate` and `endDate` are provided, `cycleDuration` is the number of days between dates.

    There is no need to adjust for `shortFallowDuration`.

    Parameters
    ----------
    start_date : str
        The start date of the Cycle, with format YYYY-MM-DD.
    end_date : str
        The end date of the Cycle, with format YYYY-MM-DD.

    Returns
    -------
    float
        The length of the Cycle, days.
    """
    start_date = parse_gapfilled_datestr(start_date)
    end_date = parse_gapfilled_datestr(end_date, "end")
    return to_precision(
        diff_in(start_date, end_date, unit=TimeUnit.DAY, add_second=True, calendar=True)
    )


def _run_with_one_year_prior():
    """Duration equals one year."""
    return _YEAR


def _calc_with_multicropping(
    single_cropped: float, double_cropped: float, triple_cropped: float
) -> float:
    """
    Calculate the average `cycleDuration` via a weighted average of multicropping Practices.
    """
    return weighted_average(
        [
            (_SINGLE_CROPPED_DURATION, single_cropped),
            (_DOUBLE_CROPPED_DURATION, double_cropped),
            (_TRIPLE_CROPPED_DURATION, triple_cropped),
        ]
    )


def _run_with_multicropping(
    single_cropped: float,
    double_cropped: float,
    triple_cropped: float,
    short_fallow_adjustment: float = 0,
) -> float:
    """
    In cases where `cycle.startDate` and `cycle.endDate` are not available, `cycleDuration` can be derived from the
    multicropping Practices: `singleCropped`, `doubleCropped`, and `tripleCropped`.

    Because multicropping Practices describe the number of harvests per year, the duration derived from them will
    include short fallow. Cycles with `startDateDefinition` = `soil preparation date`, `sowing date` or
    `transplanting date` do **not** include short fallow in their `cycleDuration`. The optional parameter
    `short_fallow_adjustment` can be used to add or remove days to account for this discrepancy.

    Parameters
    ----------
    single_cropped : float
        The area of land under a single cropping regime, % area.
    double_cropped : float
        The area of land under a double cropping regime, % area.
    triple_cropped : float
        The area of land under a triple cropping regime, % area.
    short_fallow_adjustment : float
        The number of days to add or remove to adjust for the short fallow duration, days

    Returns
    -------
    float
        The length of the Cycle, days.
    """
    duration = _calc_with_multicropping(single_cropped, double_cropped, triple_cropped)
    return to_precision(duration + short_fallow_adjustment)


def _run_with_croppingIntensity(ratio: float, short_fallow_adjustment: float = 0):
    """
    In cases where `cycle.startDate` and `cycle.endDate` are not available, `cycleDuration` can be derived from the
    Practice `croppingIntensity`.

    Because the `croppingIntensity` Practice describes the number of harvests per year, the duration derived from it
    will include short fallow. Cycles with `startDateDefinition` = `soil preparation date`, `sowing date` or
    `transplanting date` do **not** include short fallow in their `cycleDuration`. The optional parameter
    `short_fallow_adjustment` can be used to add or remove days to account for this discrepancy.

    Parameters
    ----------
    ratio : float
        Number of harvests per year. For temporary crops this is the value of `croppingIntensity` (or one if no value
        is available); for permanent crops this value is always 1.
    short_fallow_adjustment : float
        The number of days to add or remove to adjust for the short fallow duration, days

    Returns
    -------
    float
        The length of the Cycle, days.
    """
    duration = _YEAR * ratio
    return to_precision(duration + short_fallow_adjustment)


def _should_run_with_startDate_endDate(cycle: dict):
    """
    Determine whether it is possible to calculate `cycleDuration` using `cycle.startDate` and `cycle.endDate`.

    Parameters
    ----------
    cycle : dict

    Returns
    -------
    should_run : bool
    start_date : str
    end_date : str
    """
    start_date = cycle.get("startDate", "")
    start_date_has_day = validate_datestr_format(
        start_date, DatestrFormat.YEAR_MONTH_DAY
    )
    end_date = cycle.get("endDate", "")
    end_date_has_day = validate_datestr_format(end_date, DatestrFormat.YEAR_MONTH_DAY)

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="startDate endDate",
        start_date=format_str(start_date),
        start_date_has_day=format_conditional_message(
            start_date_has_day,
            on_true="True",
            on_false="False (requires format YYYY-MM-DD)",
        ),
        end_date=format_str(end_date),
        end_date_has_day=format_conditional_message(
            end_date_has_day,
            on_true="True",
            on_false="False (requires format YYYY-MM-DD)",
        ),
    )

    should_run = all([start_date_has_day, end_date_has_day])
    logShouldRun(
        cycle,
        MODEL,
        None,
        should_run,
        key=MODEL_KEY,
        by="startDate endDate",
    )
    return should_run, start_date, end_date


def _should_run_with_one_year_prior(cycle: dict):
    """
    Determine whether it is possible to calculate `cycleDuration` using `startDateDefinition` == `one year prior`.

    Parameters
    ----------
    cycle : dict

    Returns
    -------
    should_run : bool
    """
    start_date = cycle.get("startDate")
    start_date_definition = cycle.get("startDateDefinition")

    is_one_year_prior = (
        start_date_definition == CycleStartDateDefinition.ONE_YEAR_PRIOR.value
    )

    # Should not run if potentially conflicting startDate
    no_start_date = start_date is None

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="one year prior",
        start_date=format_str(start_date),
        no_start_date=format_conditional_message(
            no_start_date,
            on_true="True (method can run)",
            on_false="False (method cannot run on Cycles with a startDate)",
        ),
        start_date_definition=format_str(start_date_definition),
        is_one_year_prior=format_conditional_message(
            is_one_year_prior,
            on_true="True (method can run)",
            on_false="False (startDateDefinition must be 'one year prior')",
        ),
    )

    should_run = all([no_start_date, is_one_year_prior])

    logShouldRun(
        cycle,
        MODEL,
        None,
        should_run,
        key=MODEL_KEY,
        by="one year prior",
    )

    return (should_run,)


def _calc_short_fallow_adjustment(
    short_fallow_duration: float,
    start_date_definition: str,
    is_crop: bool,
    is_permanent: bool,
):
    """
    Cycles with `startDateDefinition` = `soil preparation date`, `sowing date` or `transplanting date` do **not**
    include short fallow duration in their `cycleDuration`.

    When gapfilling `cycleDuration` of a Cycle with temporary crops using the cropping intensity or multicropping
    methods, we must adjust the value to account for this exclusion.
    """
    short_fallow_not_in_cycleDuration = (
        start_date_definition in _START_DATE_DEFINITIONS_EXCLUDE_SHORT_FALLOW_DURATION
    )
    should_run = (
        short_fallow_duration
        and is_crop
        and not is_permanent
        and short_fallow_not_in_cycleDuration
    )
    return short_fallow_duration * -1 if should_run else 0


def _should_run_with_multicropping(cycle: dict):
    """
    Determine whether it is possible to calculate `cycleDuration` using `singleCropped`, `doubleCropped` and
    `tripleCropped` Practices.

    Parameters
    ----------
    cycle : dict

    Returns
    -------
    should_run : bool
    single_cropped : float
    double_cropped : float
    triple_cropped : float
    short_fallow_adjustment : float
    """
    practices = cycle.get("practices", [])

    product = find_primary_product(cycle) or {}
    product_term = product.get("term", {})
    is_primary_product_crop = product_term.get("termType") == TermTermType.CROP.value
    is_permanent = is_permanent_crop(MODEL, MODEL_KEY, product_term)

    single_cropped = get_node_value(find_term_match(practices, _SINGLE_CROPPED_TERM_ID))
    double_cropped = get_node_value(find_term_match(practices, _DOUBLE_CROPPED_TERM_ID))
    triple_cropped = get_node_value(find_term_match(practices, _TRIPLE_CROPPED_TERM_ID))

    multicropping_sum_is_100 = sum_is_100(
        single_cropped, double_cropped, triple_cropped
    )

    start_date_definition = cycle.get("startDateDefinition")
    short_fallow_duration = get_node_value(
        find_term_match(practices, _SHORT_FALLOW_DURATION_TERM_ID), default=None
    )
    start_date_definition = cycle.get("startDateDefinition")
    short_fallow_duration = get_node_value(
        find_term_match(practices, _SHORT_FALLOW_DURATION_TERM_ID), default=None
    )
    short_fallow_adjustment = _calc_short_fallow_adjustment(
        short_fallow_duration,
        start_date_definition,
        is_primary_product_crop,
        is_permanent,
    )

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="multicropping",
        is_primary_product_crop=format_bool(is_primary_product_crop),
        is_permanent=format_conditional_message(
            is_permanent,
            on_true="True (invalid for multicropping calculation)",
            on_false="False (valid for multicropping calculation)",
        ),
        single_cropped=format_float(single_cropped, "pct area"),
        double_cropped=format_float(double_cropped, "pct area"),
        triple_cropped=format_float(triple_cropped, "pct area"),
        multicropping_sum_is_100=format_conditional_message(
            multicropping_sum_is_100,
            on_true="True",
            on_false="False (sum of multicropping practices must equal 100)",
        ),
        start_date_definition=format_str(start_date_definition),
        short_fallow_duration=format_float(short_fallow_duration, "days"),
        short_fallow_adjustment=format_float(short_fallow_adjustment, "days"),
    )

    should_run = all(
        [
            is_primary_product_crop,
            not is_permanent,
            multicropping_sum_is_100,
        ]
    )

    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY, by="multicropping")

    return (
        should_run,
        single_cropped,
        double_cropped,
        triple_cropped,
        short_fallow_adjustment,
    )


def _should_run_with_croppingIntensity(cycle: dict):
    """
    Determine whether it is possible to calculate `cycleDuration` using the `croppingIntensity` Practice.

    Parameters
    ----------
    cycle : dict

    Returns
    -------
    should_run : bool
    ratio : float
    short_fallow_adjustment : float
    """
    practices = cycle.get("practices", [])

    product = find_primary_product(cycle) or {}
    product_term = product.get("term", {})
    is_primary_product_crop = product_term.get("termType") == TermTermType.CROP.value
    is_permanent = is_permanent_crop(MODEL, MODEL_KEY, product_term)

    cropping_intensity = get_node_value(
        find_term_match(practices, _CROPPING_INTENSITY_TERM_ID), default=None
    )
    ratio = (
        _PERMANENT_RATIO
        if is_permanent
        else (cropping_intensity or _DEFAULT_TEMPORARY_RATIO)
    )

    start_date_definition = cycle.get("startDateDefinition")
    short_fallow_duration = get_node_value(
        find_term_match(practices, _SHORT_FALLOW_DURATION_TERM_ID), default=None
    )
    short_fallow_adjustment = _calc_short_fallow_adjustment(
        short_fallow_duration,
        start_date_definition,
        is_primary_product_crop,
        is_permanent,
    )

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="croppingIntensity",
        is_primary_product_crop=format_bool(is_primary_product_crop),
        is_permanent=format_conditional_message(
            is_permanent,
            on_true="True (ratio is 1)",
            on_false="False (ratio is cropping intensity)",
        ),
        cropping_intensity=format_float(cropping_intensity),
        ratio=format_float(ratio),
        start_date_definition=format_str(start_date_definition),
        short_fallow_duration=format_float(short_fallow_duration, "days"),
        short_fallow_adjustment=format_float(short_fallow_adjustment, "days"),
    )

    should_run = all([is_primary_product_crop])
    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY, by="croppingIntensity")
    return should_run, ratio, short_fallow_adjustment


CALC_STRATEGIES = {
    _should_run_with_startDate_endDate: _run_with_startDate_endDate,
    _should_run_with_one_year_prior: _run_with_one_year_prior,
    _should_run_with_multicropping: _run_with_multicropping,
    _should_run_with_croppingIntensity: _run_with_croppingIntensity,
}
"""
A mapping between `_should_run` and `_run` functions for each run strategy.
"""


def _should_run(cycle: dict):
    """
    Extract data from Cycle node and determine whether the model should run.
    """
    run_func, *args = select_run_func(CALC_STRATEGIES, cycle)
    should_run = all([run_func is not None])
    return should_run, run_func, *args


def run(cycle: dict):
    """
    Run the model on a Cycle.
    """
    should_run, run_func, *args = _should_run(cycle)
    return run_func(*args) if should_run else None
