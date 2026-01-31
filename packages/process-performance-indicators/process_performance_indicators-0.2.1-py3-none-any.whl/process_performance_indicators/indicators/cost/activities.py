from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.cost.instances as cost_instances_indicators
import process_performance_indicators.indicators.general.activities as general_activities_indicators
import process_performance_indicators.indicators.quality.activities as quality_activities_indicators
import process_performance_indicators.indicators.time.activities as time_activities_indicators
import process_performance_indicators.utils.activities as activities_utils
import process_performance_indicators.utils.cases_activities as cases_activities_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils.safe_division import safe_division


def fixed_cost(event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The fixed cost associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    aggregation_function = {
        "sgl": cost_instances_indicators.fixed_cost_for_single_events_of_activity_instances,
        "sum": cost_instances_indicators.fixed_cost_for_sum_of_all_events_of_activity_instances,
    }
    total_fixed_cost = 0
    activity_instances = activities_utils.inst(event_log, activity_name)

    for instance_id in activity_instances:
        aggregate_value = aggregation_function[aggregation_mode](event_log, instance_id) or 0
        total_fixed_cost += aggregate_value

    return total_fixed_cost


def human_resource_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of human resources that are involved in the execution of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.

    """
    return len(activities_utils.hres(event_log, activity_name))


def inventory_cost(event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The inventory cost associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    aggregation_function = {
        "sgl": cost_instances_indicators.inventory_cost_for_single_events_of_activity_instances,
        "sum": cost_instances_indicators.inventory_cost_for_sum_of_all_events_of_activity_instances,
    }
    total_inventory_cost = 0

    for instance_id in activities_utils.inst(event_log, activity_name):
        total_inventory_cost += aggregation_function[aggregation_mode](event_log, instance_id) or 0

    return total_inventory_cost


def labor_cost_and_total_cost_ratio(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the labor cost associated with all instantiations of the activity,
    and the total cost associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        labor_cost(event_log, activity_name, aggregation_mode),
        total_cost(event_log, activity_name, aggregation_mode),
    )


def labor_cost(event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The labor cost associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    aggregation_function = {
        "sgl": cost_instances_indicators.labor_cost_for_single_events_of_activity_instances,
        "sum": cost_instances_indicators.labor_cost_for_sum_of_all_events_of_activity_instances,
    }
    labor_cost = 0

    for instance_id in activities_utils.inst(event_log, activity_name):
        labor_cost += aggregation_function[aggregation_mode](event_log, instance_id) or 0

    return labor_cost


def resource_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of resources that are involved in the execution of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.

    """
    return len(activities_utils.res(event_log, activity_name))


def rework_cost(event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The total cost of all times that the activity has been instantiated again, after its
    first instantiation, in any case.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    sum_of_first_occurrences_cost = 0
    for case_id in event_log[StandardColumnNames.CASE_ID].unique():
        sum_of_first_occurrences_cost += cases_activities_utils.fitc(
            event_log, case_id, activity_name, aggregation_mode
        )

    return total_cost(event_log, activity_name, aggregation_mode) - sum_of_first_occurrences_cost


def rework_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of times that the activity has been instantiated again, after its first
    intantiation, in any case.

    Args:
        event_log: The event log.
        activity_name: The activity name.

    """
    rework_count = 0

    for case_id in event_log[StandardColumnNames.CASE_ID].unique():
        rework_count += max(0, cases_activities_utils.count(event_log, case_id, activity_name) - 1)
    return rework_count


def rework_percentage(event_log: pd.DataFrame, activity_name: str) -> float:
    """
    The percentage of times that the activity has been instantiated again, after its first
    instantiation, in any case.

    Args:
        event_log: The event log.
        activity_name: The activity name.

    """
    return safe_division(
        rework_count(event_log, activity_name),
        general_activities_indicators.activity_instance_count(event_log, activity_name),
    )


def total_cost(event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The total cost associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    aggregation_function = {
        "sgl": cost_instances_indicators.total_cost_for_single_events_of_activity_instances,
        "sum": cost_instances_indicators.total_cost_for_sum_of_all_events_of_activity_instances,
    }
    total_cost: float = 0

    for instance_id in activities_utils.inst(event_log, activity_name):
        total_cost += aggregation_function[aggregation_mode](event_log, instance_id) or 0

    return total_cost


def total_cost_and_lead_time_ratio(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all instantiations of the activity, and the
    sum of total elapsed times for all instantiations of the activity. In cost per hour.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    # TODO : ask here if calculation is correct
    return safe_division(
        total_cost(event_log, activity_name, aggregation_mode),
        time_activities_indicators.lead_time(event_log, activity_name) / pd.Timedelta(hours=1),
    )


def total_cost_and_outcome_unit_ratio(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all instantiations of the activity, and the
    outcome units associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost and outcome unit calculations.
            "sum": Considers the sum of all events of activity instances for cost and outcome unit calculations.

    """
    return safe_division(
        total_cost(event_log, activity_name, aggregation_mode),
        quality_activities_indicators.outcome_unit_count(event_log, activity_name, aggregation_mode),
    )


def total_cost_and_service_time_ratio(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all instantiations of the activity, and the
    sum of elapsed times between the start and complete events of all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        total_cost(event_log, activity_name, aggregation_mode),
        time_activities_indicators.service_time(event_log, activity_name) / pd.Timedelta(hours=1),
    )


def variable_cost(event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The variable cost associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The activity name.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    aggregation_function = {
        "sgl": cost_instances_indicators.variable_cost_for_single_events_of_activity_instances,
        "sum": cost_instances_indicators.variable_cost_for_sum_of_all_events_of_activity_instances,
    }
    variable_cost = 0

    for instance_id in activities_utils.inst(event_log, activity_name):
        variable_cost += aggregation_function[aggregation_mode](event_log, instance_id) or 0

    return variable_cost
