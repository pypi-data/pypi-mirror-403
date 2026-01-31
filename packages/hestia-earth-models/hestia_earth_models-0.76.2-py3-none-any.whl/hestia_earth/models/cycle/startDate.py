from datetime import timedelta
from typing import Optional

from hestia_earth.schema import CycleStartDateDefinition

from hestia_earth.utils.date import (
    convert_datestr,
    DatestrFormat,
    validate_datestr_format,
    parse_gapfilled_datestr,
)

from hestia_earth.models.utils import select_run_func
from hestia_earth.models.log import (
    format_float,
    format_str,
    logRequirements,
    logShouldRun,
)
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "none": {"startDate": "in day precision"},
        "optional": {
            "or": [
                {
                    "endDate": "in day precision",
                    "cycleDuration": "",
                },
                {"endDate": "", "startDateDefinition": "start of year"},
            ]
        },
    }
}
RETURNS = {"The startDate as a string": ""}
MODEL_KEY = "startDate"


def _run_by_cycleDuration(end_date: str, cycle_duration: float):
    endDate = parse_gapfilled_datestr(end_date, "end")
    days = max(cycle_duration - 1, 1)
    return (endDate - timedelta(days=days)).strftime(DatestrFormat.YEAR_MONTH_DAY.value)


def _run_by_startDate(start_date: str, end_date: Optional[str]):
    is_same_month = start_date == (end_date or "")[:7]
    # start of the month if same month as end date
    return f"{start_date}-01" if is_same_month else f"{start_date}-15"


def _run_by_start_of_year(end_date: str):
    year = end_date[0:4]  # just the year component
    return convert_datestr(year, DatestrFormat.YEAR_MONTH_DAY)


def _should_run_by_cycleDuration(cycle: dict):
    end_date = cycle.get("endDate")
    cycle_duration = cycle.get("cycleDuration")

    has_endDate = end_date is not None
    has_endDate_day_precision = has_endDate and validate_datestr_format(
        end_date, DatestrFormat.YEAR_MONTH_DAY
    )
    has_cycleDuration = cycle_duration is not None

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="cycleDuration",
        end_date=format_str(end_date),
        has_endDate_day_precision=has_endDate_day_precision,
        cycle_duration=format_float(cycle_duration),
    )

    should_run = all([has_endDate, has_endDate_day_precision, has_cycleDuration])
    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY, by="cycleDuration")
    return should_run, end_date, cycle_duration


def _should_run_by_startDate(cycle: dict):
    start_date = cycle.get("startDate")
    end_date = cycle.get("endDate")
    cycle_duration = cycle.get("cycleDuration")

    has_startDate = start_date is not None
    has_month_precision = has_startDate and validate_datestr_format(
        start_date, DatestrFormat.YEAR_MONTH
    )
    no_cycleDuration = cycle_duration is None

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="startDate",
        start_date=start_date,
        has_month_precision=has_month_precision,
        no_cycleDuration=no_cycleDuration,
    )

    should_run = all([has_startDate, has_month_precision, no_cycleDuration])
    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY, by="startDate")
    return should_run, start_date, end_date


def _should_run_by_start_of_year(cycle: dict):
    start_date = cycle.get("startDate")
    end_date = cycle.get("endDate")
    cycle_duration = cycle.get("cycleDuration")
    start_date_definition = cycle.get("startDateDefinition")

    has_endDate = end_date is not None
    is_start_of_year = (
        start_date_definition == CycleStartDateDefinition.START_OF_YEAR.value
    )
    no_startDate = start_date is None
    no_cycleDuration = cycle_duration is None

    logRequirements(
        cycle,
        model=MODEL,
        key=MODEL_KEY,
        by="start of year",
        start_date_definition=start_date_definition,
        is_start_of_year=is_start_of_year,
        end_date=end_date,
        cycle_duration=cycle_duration,
    )

    should_run = all([has_endDate, is_start_of_year, no_cycleDuration, no_startDate])
    logShouldRun(cycle, MODEL, None, should_run, key=MODEL_KEY, by="start of year")
    return should_run, end_date


CALC_STRATEGIES = {
    _should_run_by_cycleDuration: _run_by_cycleDuration,
    _should_run_by_startDate: _run_by_startDate,
    _should_run_by_start_of_year: _run_by_start_of_year,
}
"""
A mapping between `_should_run` and `_run` functions for each run strategy.
"""


def _has_complete_startDate(cycle: dict):
    start_date = cycle.get("startDate")
    return bool(start_date) and validate_datestr_format(
        start_date, DatestrFormat.YEAR_MONTH_DAY
    )


def _should_run(cycle: dict):
    """
    Extract data from Cycle node and determine whether the model should run.
    """
    run_func, *args = (
        select_run_func(CALC_STRATEGIES, cycle)
        if not _has_complete_startDate(cycle)
        else (None,)
    )
    should_run = all([run_func is not None])
    return should_run, run_func, *args


def run(cycle: dict):
    should_run, run_func, *args = _should_run(cycle)
    return run_func(*args) if should_run else None
