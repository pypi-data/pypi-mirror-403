from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.cost.activities as cost_activities_indicators
import process_performance_indicators.indicators.flexibility.activities as flexibility_activities_indicators
import process_performance_indicators.indicators.general.activities as general_activities_indicators
import process_performance_indicators.indicators.quality.instances as quality_instances_indicators
import process_performance_indicators.indicators.time.activities as time_activities_indicators
import process_performance_indicators.utils.activities as activities_utils
import process_performance_indicators.utils.cases_activities as cases_activities_utils
import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils.safe_division import safe_division


def activity_instance_count_by_human_resource(
    event_log: pd.DataFrame, activity_name: str, human_resource_name: str
) -> int:
    """
    The number of times that a specific activity is instantiated by a specific human resource in the event log.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        human_resource_name: The name of the human resource.

    """
    activity_instances = activities_utils.inst(event_log, activity_name)
    activity_instances_instantiated_by_human_resource = set()
    for instance_id in activity_instances:
        if instances_utils.hres(event_log, instance_id) == human_resource_name:
            activity_instances_instantiated_by_human_resource.add(instance_id)
    return len(activity_instances_instantiated_by_human_resource)


def client_count_and_total_cost_ratio(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the number of distinct clients associated with cases where the activity is instantiated,
    and the total cost associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = flexibility_activities_indicators.client_count(event_log, activity_name)
    denominator = cost_activities_indicators.total_cost(event_log, activity_name, aggregation_mode)
    return safe_division(numerator, denominator)


def human_resource_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of human resources that are involved in the execution of the activity.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    return len(activities_utils.hres(event_log, activity_name))


def outcome_unit_count(event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The outcome units associated with all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit calculations.

    """
    aggregation_function = {
        "sgl": quality_instances_indicators.outcome_unit_count_for_single_events_of_activity_instances,
        "sum": quality_instances_indicators.outcome_unit_count_for_sum_of_all_events_of_activity_instances,
    }
    activity_instances = activities_utils.inst(event_log, activity_name)

    outcome_unit_count = 0
    for instance_id in activity_instances:
        outcome_unit = aggregation_function[aggregation_mode](event_log, instance_id)
        if outcome_unit is not None:
            outcome_unit_count += outcome_unit
    return outcome_unit_count


def rework_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of times that the activity has been instantiated again, after its first instantiation, in any case.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    rework_count = 0

    for case_id in event_log[StandardColumnNames.CASE_ID].unique():
        rework_count += max(0, cases_activities_utils.count(event_log, case_id, activity_name) - 1)
    return rework_count


def rework_count_by_value(event_log: pd.DataFrame, activity_name: str, value: float) -> float:
    """
    The number of times that the activity has been instantiated again, after it has been instantiated a certain number of times, in any case.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        value: The certain number of times that the activity has been instantiated.

    """
    rework_count = 0
    for case_id in event_log[StandardColumnNames.CASE_ID].unique():
        rework_count += max(0, cases_activities_utils.count(event_log, case_id, activity_name) - value)
    return rework_count


def rework_percentage(event_log: pd.DataFrame, activity_name: str) -> float:
    """
    The percentage of times that the activity has been instantiated again, after its first instantiation, in any case.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    numerator = rework_count(event_log, activity_name)
    denominator = general_activities_indicators.activity_instance_count(event_log, activity_name)
    return safe_division(numerator, denominator)


def rework_percentage_by_value(event_log: pd.DataFrame, activity_name: str, value: float) -> float:
    """
    The percentage of times that the activity has been instantiated again, after it has been instantiated
    a certain number of times, in any case.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        value: The certain number of times that the activity has been instantiated.

    """
    numerator = rework_count_by_value(event_log, activity_name, value)
    denominator = general_activities_indicators.activity_instance_count(event_log, activity_name)
    return safe_division(numerator, denominator)


def rework_time(event_log: pd.DataFrame, activity_name: str) -> pd.Timedelta:
    """
    The total elapsed time for all times that the activity has been instantiated again, after its first instantiation, in any case.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    sum_of_first_occurrences_times = pd.Timedelta(0)
    for case_id in event_log[StandardColumnNames.CASE_ID].unique():
        sum_of_first_occurrences_times += cases_activities_utils.filt(event_log, case_id, activity_name)

    return time_activities_indicators.lead_time(event_log, activity_name) - sum_of_first_occurrences_times


def successful_outcome_unit_count(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> int:
    """
    The outcome units associated with all instantiations of the activity, after deducting those that were unsuccessfully completed.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    sum_of_successful_outcome_unit_counts = 0
    for instance_id in activities_utils.inst(event_log, activity_name):
        sum_of_successful_outcome_unit_counts += quality_instances_indicators.successful_outcome_unit_count(
            event_log, instance_id, aggregation_mode
        )
    return sum_of_successful_outcome_unit_counts


def successful_outcome_unit_percentage(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The percentage of outcome units associated with all instantiations of the activity that were successfully completed.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    numerator = successful_outcome_unit_count(event_log, activity_name, aggregation_mode)
    denominator = outcome_unit_count(event_log, activity_name, aggregation_mode)
    return safe_division(numerator, denominator)


def total_cost_and_client_count_ratio(
    event_log: pd.DataFrame, activity_name: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all instantiations of the activity, and the number of distinct clients associated with cases where the activity is instantiated.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = cost_activities_indicators.total_cost(event_log, activity_name, aggregation_mode)
    denominator = flexibility_activities_indicators.client_count(event_log, activity_name)
    return safe_division(numerator, denominator)
