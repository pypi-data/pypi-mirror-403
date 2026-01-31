import pandas as pd

from process_performance_indicators.constants import (
    LifecycleTransitionType,
    StandardColumnNames,
)
from process_performance_indicators.formatting.instance_id_generator import id_generator


def match_all(case_log: pd.DataFrame) -> None:
    """
    Match all complete events in the case log to their corresponding start events.

    Args:
        case_log: The event log to match.

    """
    complete_events = case_log[case_log[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.COMPLETE]
    for _, complete_event in complete_events.iterrows():
        _match(case_log, complete_event)


def _match(case_log: pd.DataFrame, complete_event: pd.Series) -> None:
    """
    Match a complete event to its corresponding start event.

    Args:
        case_log: The case log of the complete event to match.
        complete_event: The complete event to match

    """
    if complete_event[StandardColumnNames.LIFECYCLE_TRANSITION] != LifecycleTransitionType.COMPLETE:
        error_message = "The provided event is not a complete event"
        raise ValueError(error_message)

    # Create a unique instance ID for the complete event
    instance_id = id_generator.get_next_id()
    case_log.loc[[complete_event.name], StandardColumnNames.INSTANCE.value] = instance_id

    compatible_start_events = _compatible_start_events(case_log, complete_event)

    # If there are no compatible start events, do nothing
    if compatible_start_events.empty:
        return

    # Match the complete event to the first compatible start event
    matching_start_event_index = compatible_start_events.index[0]
    case_log.loc[[matching_start_event_index], StandardColumnNames.INSTANCE.value] = instance_id


def _compatible_start_events(case_log: pd.DataFrame, complete_event: pd.Series) -> pd.DataFrame:
    """
    Find all start events in the case log that are compatible with the complete event.

    Args:
        case_log: The event log to search.
        complete_event: The complete event to match.

    Returns:
        The compatible start events.

    """
    activity = complete_event[StandardColumnNames.ACTIVITY]
    complete_timestamp = complete_event[StandardColumnNames.TIMESTAMP]

    # Find all start events that are compatible with the complete event
    potential_matches = case_log[
        (case_log[StandardColumnNames.ACTIVITY] == activity)
        & (case_log[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.START)
        & (case_log[StandardColumnNames.TIMESTAMP] <= complete_timestamp)
        & (case_log[StandardColumnNames.INSTANCE].isna())
    ]

    return potential_matches.sort_values(by=StandardColumnNames.TIMESTAMP, ascending=True)
