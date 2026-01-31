from typing import Literal

import pandas as pd

import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils.column_validation import assert_column_exists
from process_performance_indicators.utils.safe_division import safe_division


def outcome_unit_count_for_single_events_of_activity_instances(
    event_log: pd.DataFrame, instance_id: str
) -> float | None:
    """
    The outcome units associated with an activity instance, measured as the latest recorded value among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.OUTCOME_UNIT)
    complete_event = instances_utils.cpl(event_log, instance_id)
    if not complete_event.empty:
        return float(complete_event[StandardColumnNames.OUTCOME_UNIT].unique()[0])

    start_event = instances_utils.start(event_log, instance_id)
    if not start_event.empty:
        return float(start_event[StandardColumnNames.OUTCOME_UNIT].unique()[0])

    return None


def outcome_unit_count_for_sum_of_all_events_of_activity_instances(
    event_log: pd.DataFrame, instance_id: str
) -> float | None:
    """
    The outcome units associated with an activity instance, measured as the sum of all values among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.OUTCOME_UNIT)
    start_event = instances_utils.start(event_log, instance_id)
    complete_event = instances_utils.cpl(event_log, instance_id)
    if not start_event.empty and not complete_event.empty:
        return float(
            start_event[StandardColumnNames.OUTCOME_UNIT].unique()[0]
            + complete_event[StandardColumnNames.OUTCOME_UNIT].unique()[0]
        )
    return None


def successful_outcome_unit_count(
    event_log: pd.DataFrame, instance_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> int:
    """
    The outcome units associated with an activity instance, after deducting those that were unsuccessfully completed.

    Args:
        event_log: The event log.
        instance_id: The instance id.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    aggregation_function = {
        "sgl": outcome_unit_count_for_single_events_of_activity_instances,
        "sum": outcome_unit_count_for_sum_of_all_events_of_activity_instances,
    }
    outcome_unit_count = aggregation_function[aggregation_mode](event_log, instance_id)
    complete_event = instances_utils.cpl(event_log, instance_id)
    if not complete_event.empty:
        return outcome_unit_count - float(complete_event[StandardColumnNames.UNSUCCESSFUL_OUTCOME_UNIT].unique()[0])

    return outcome_unit_count


def successful_outcome_unit_percentage(
    event_log: pd.DataFrame, instance_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The percentage of outcome units associated with an activity instance that were successfully completed.

    Args:
        event_log: The event log.
        instance_id: The instance id.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    # TODO: check here what to do if denominator is None
    outcome_unit_function = {
        "sgl": outcome_unit_count_for_single_events_of_activity_instances,
        "sum": outcome_unit_count_for_sum_of_all_events_of_activity_instances,
    }

    numerator = successful_outcome_unit_count(event_log, instance_id, aggregation_mode)
    denominator = outcome_unit_function[aggregation_mode](event_log, instance_id)
    return safe_division(numerator, denominator)
