from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.quality.instances as quality_instances_indicators
import process_performance_indicators.indicators.time.instances as time_instances_indicators
import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils import assert_column_exists
from process_performance_indicators.utils.safe_division import safe_division


def fixed_cost_for_single_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The fixed cost associated with an activity instance, measured as the latest recorded value
    among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    Returns:
        float: The fixed cost for single events of an activity instance.
        None: If no fixed cost is found.

    """
    assert_column_exists(event_log, StandardColumnNames.FIXED_COST)

    complete_event = instances_utils.cpl(event_log, instance_id)
    if not complete_event.empty:
        return float(complete_event[StandardColumnNames.FIXED_COST].unique()[0])

    start_event = instances_utils.start(event_log, instance_id)
    if not start_event.empty:
        return float(start_event[StandardColumnNames.FIXED_COST].unique()[0])

    return None


def fixed_cost_for_sum_of_all_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The fixed cost associated with an activity instance, measured as the sum of
    all values among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.FIXED_COST)

    start_event = instances_utils.start(event_log, instance_id)
    complete_event = instances_utils.cpl(event_log, instance_id)

    if not start_event.empty and not complete_event.empty:
        return float(
            start_event[StandardColumnNames.FIXED_COST].unique()[0]
            + complete_event[StandardColumnNames.FIXED_COST].unique()[0]
        )

    return None


def inventory_cost_for_single_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The inventory cost associated with an activity instance, measured as the latest
    recorded value among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.INVENTORY_COST)

    complete_event = instances_utils.cpl(event_log, instance_id)
    if not complete_event.empty:
        return float(complete_event[StandardColumnNames.INVENTORY_COST].unique()[0])

    start_event = instances_utils.start(event_log, instance_id)
    if not start_event.empty:
        return float(start_event[StandardColumnNames.INVENTORY_COST].unique()[0])

    return None


def inventory_cost_for_sum_of_all_events_of_activity_instances(
    event_log: pd.DataFrame, instance_id: str
) -> float | None:
    """
    The inventory cost associated with an activity instance, measured as the sum of
    all values among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.INVENTORY_COST)

    start_event = instances_utils.start(event_log, instance_id)
    complete_event = instances_utils.cpl(event_log, instance_id)

    if not start_event.empty and not complete_event.empty:
        return float(
            start_event[StandardColumnNames.INVENTORY_COST].unique()[0]
            + complete_event[StandardColumnNames.INVENTORY_COST].unique()[0]
        )

    return None


def labor_cost_and_total_cost_ratio(
    event_log: pd.DataFrame, instance_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the labor cost associated with the activity instance, and the total cost
    associated with the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.
        aggregation_mode: The aggregation mode.
            "sgl": The aggregation mode for single events of an activity instance.
            "sum": The aggregation mode for the sum of all events of an activity instance.

    """
    # TODO: ask here what to do when labor_cost or total_cost is None
    assert_column_exists(event_log, StandardColumnNames.LABOR_COST)
    assert_column_exists(event_log, StandardColumnNames.TOTAL_COST)

    aggregation_functions = {
        "sgl": (
            labor_cost_for_single_events_of_activity_instances,
            total_cost_for_single_events_of_activity_instances,
        ),
        "sum": (
            labor_cost_for_sum_of_all_events_of_activity_instances,
            total_cost_for_sum_of_all_events_of_activity_instances,
        ),
    }

    labor_cost_func, total_cost_func = aggregation_functions[aggregation_mode]
    labor_cost = labor_cost_func(event_log, instance_id)
    total_cost = total_cost_func(event_log, instance_id)

    return safe_division(labor_cost, total_cost)


def labor_cost_for_single_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The labor cost associated with an activity instance, measured as the lastest recorded value among the events
    of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.LABOR_COST)

    complete_event = instances_utils.cpl(event_log, instance_id)
    if not complete_event.empty:
        return float(complete_event[StandardColumnNames.LABOR_COST].unique()[0])

    start_event = instances_utils.start(event_log, instance_id)
    if not start_event.empty:
        return float(start_event[StandardColumnNames.LABOR_COST].unique()[0])

    return None


def labor_cost_for_sum_of_all_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The labor cost associated with an activity instance, measured as the sum of
    all values among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.LABOR_COST)

    start_event = instances_utils.start(event_log, instance_id)
    complete_event = instances_utils.cpl(event_log, instance_id)

    if not start_event.empty and not complete_event.empty:
        return float(
            start_event[StandardColumnNames.LABOR_COST].unique()[0]
            + complete_event[StandardColumnNames.LABOR_COST].unique()[0]
        )

    return None


def total_cost_for_single_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The total cost associated with an activity instance, measured as the lastest recorded
    value among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.TOTAL_COST)

    complete_event = instances_utils.cpl(event_log, instance_id)
    if not complete_event.empty:
        return float(complete_event[StandardColumnNames.TOTAL_COST].unique()[0])

    start_event = instances_utils.start(event_log, instance_id)
    if not start_event.empty:
        return float(start_event[StandardColumnNames.TOTAL_COST].unique()[0])

    return None


def total_cost_for_sum_of_all_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The total cost associated with an activity instance, measured as the sum of
    all values among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.TOTAL_COST)

    start_event = instances_utils.start(event_log, instance_id)
    complete_event = instances_utils.cpl(event_log, instance_id)

    if not start_event.empty and not complete_event.empty:
        return float(
            start_event[StandardColumnNames.TOTAL_COST].unique()[0]
            + complete_event[StandardColumnNames.TOTAL_COST].unique()[0]
        )

    return None


def total_cost_and_lead_time_ratio(
    event_log: pd.DataFrame, instance_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with the activity instance, and the total elapsed
    time of the activity instance. In cost per hour.

    Args:
        event_log: The event log.
        instance_id: The instance id.
        aggregation_mode: The aggregation mode.
            "sgl": The aggregation mode for single events of an activity instance.
            "sum": The aggregation mode for the sum of all events of an activity instance.

    """
    assert_column_exists(event_log, StandardColumnNames.TOTAL_COST)

    # TODO: ask here what to do when total_cost is None
    total_cost_function = {
        "sgl": total_cost_for_single_events_of_activity_instances,
        "sum": total_cost_for_sum_of_all_events_of_activity_instances,
    }

    return safe_division(
        total_cost_function[aggregation_mode](event_log, instance_id),
        time_instances_indicators.lead_time(event_log, instance_id) / pd.Timedelta(hours=1),
    )


def total_cost_and_outcome_unit_ratio(
    event_log: pd.DataFrame, instance_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with the activity instance, and the outcome
    units associated with the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost and outcome unit calculations.
            "sum": Considers the sum of all events of activity instances for cost and outcome unit calculations.

    """
    assert_column_exists(event_log, StandardColumnNames.TOTAL_COST)

    aggregation_functions = {
        "sgl": {
            "cost": total_cost_for_single_events_of_activity_instances,
            "outcome": quality_instances_indicators.outcome_unit_count_for_single_events_of_activity_instances,
        },
        "sum": {
            "cost": total_cost_for_sum_of_all_events_of_activity_instances,
            "outcome": quality_instances_indicators.outcome_unit_count_for_sum_of_all_events_of_activity_instances,
        },
    }

    cost_func = aggregation_functions[aggregation_mode]["cost"]
    outcome_func = aggregation_functions[aggregation_mode]["outcome"]

    total_cost = cost_func(event_log, instance_id) or 0
    outcome_unit = outcome_func(event_log, instance_id) or 0

    return safe_division(total_cost, outcome_unit)


def total_cost_and_service_time_ratio(
    event_log: pd.DataFrame, instance_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with the activity instance, and the elapsed
    time between the start and complete events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    assert_column_exists(event_log, StandardColumnNames.TOTAL_COST)

    # TODO: ask here what to do when total_cost is None
    total_cost_function = {
        "sgl": total_cost_for_single_events_of_activity_instances,
        "sum": total_cost_for_sum_of_all_events_of_activity_instances,
    }
    return safe_division(
        total_cost_function[aggregation_mode](event_log, instance_id),
        time_instances_indicators.service_time(event_log, instance_id) / pd.Timedelta(hours=1),
    )


def variable_cost_for_single_events_of_activity_instances(event_log: pd.DataFrame, instance_id: str) -> float | None:
    """
    The variable cost associated with an activity instance, measured as the latest recorded
    value among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.VARIABLE_COST)

    complete_event = instances_utils.cpl(event_log, instance_id)
    if not complete_event.empty:
        return float(complete_event[StandardColumnNames.VARIABLE_COST].unique()[0])

    start_event = instances_utils.start(event_log, instance_id)
    if not start_event.empty:
        return float(start_event[StandardColumnNames.OUTCOME_UNIT].unique()[0])

    return None


def variable_cost_for_sum_of_all_events_of_activity_instances(
    event_log: pd.DataFrame, instance_id: str
) -> float | None:
    """
    The variable cost associated with an activity instance, measured as the sum of all
    values among the events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    assert_column_exists(event_log, StandardColumnNames.VARIABLE_COST)

    start_event = instances_utils.start(event_log, instance_id)
    complete_event = instances_utils.cpl(event_log, instance_id)

    if not start_event.empty and not complete_event.empty:
        return float(
            start_event[StandardColumnNames.VARIABLE_COST].unique()[0]
            + complete_event[StandardColumnNames.VARIABLE_COST].unique()[0]
        )
    return None
