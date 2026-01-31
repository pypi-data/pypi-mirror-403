import pandas as pd

from process_performance_indicators.constants import (
    LifecycleTransitionType,
    StandardColumnNames,
)
from process_performance_indicators.formatting.match import match_all


def convert_to_derivable_interval_log(event_log: pd.DataFrame) -> pd.DataFrame:
    """
    Convert an event log into a derivable log.

    Args:
        event_log: The event log to convert.

    Returns:
        The converted event log.

    """
    if StandardColumnNames.LIFECYCLE_TRANSITION in event_log.columns:
        error_message = "Event log is not an atomic log and can't be converted to derivable interval log"
        raise ValueError(error_message)

    event_log = event_log.copy()
    # FIX: this ensures that case id is a string, check if this is the best way to do this
    event_log[StandardColumnNames.CASE_ID] = event_log[StandardColumnNames.CASE_ID].astype(str)
    event_log[StandardColumnNames.LIFECYCLE_TRANSITION] = LifecycleTransitionType.COMPLETE.value

    return event_log.reset_index(drop=True)


def convert_to_explicit_interval_log(event_log: pd.DataFrame) -> pd.DataFrame:
    """
    Convert an event log into an explicit interval log by matching start and complete events.
    Not matched start events are dropped.

    Args:
        event_log: The event log to convert. Assumes standard columns are present.

    Returns:
        The converted event log with INSTANCE IDs linking matched events.

    """
    event_log = event_log.copy()
    event_log[StandardColumnNames.CASE_ID] = event_log[StandardColumnNames.CASE_ID].astype(str)
    event_log[StandardColumnNames.INSTANCE] = pd.NA

    return (
        event_log.groupby(StandardColumnNames.CASE_ID, group_keys=False)
        .apply(_process_case_group)
        .dropna(subset=[StandardColumnNames.INSTANCE])
        .sort_values(
            by=[
                StandardColumnNames.CASE_ID,
                StandardColumnNames.TIMESTAMP,
            ],
            ascending=True,
        )
        .reset_index(drop=True)
    )


def _process_case_group(case_log: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the matching logic to a single case group.

    Args:
        case_log: The case log to process.

    Returns:
        The processed case log.

    """
    match_all(case_log)
    return case_log
