from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.general.cases as general_cases_indicators
import process_performance_indicators.indicators.quality.instances as quality_instances_indicators
import process_performance_indicators.indicators.time.cases as time_cases_indicators
import process_performance_indicators.utils.cases as cases_utils
import process_performance_indicators.utils.cases_activities as cases_activities_utils
import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils.column_validation import assert_column_exists
from process_performance_indicators.utils.safe_division import safe_division


def activity_instance_count_by_human_resource(event_log: pd.DataFrame, case_id: str, human_resource_name: str) -> int:
    """
    The number of times that any activity is instantiated by a specific human resource in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        human_resource_name: The name of the human resource.

    """
    activity_instances = cases_utils.inst(event_log, case_id)
    activity_instances_instantiated_by_human_resource = set()
    for instance_id in activity_instances:
        if instances_utils.hres(event_log, instance_id) == human_resource_name:
            activity_instances_instantiated_by_human_resource.add(instance_id)
    return len(activity_instances_instantiated_by_human_resource)


def activity_instance_count_by_role(event_log: pd.DataFrame, case_id: str, role_name: str) -> int:
    """
    The number of times that any activity is instantiated by a specific role in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        role_name: The name of the role.

    """
    activity_instances = cases_utils.inst(event_log, case_id)
    activity_instances_instantiated_by_role = set()
    for instance_id in activity_instances:
        if instances_utils.role(event_log, instance_id) == role_name:
            activity_instances_instantiated_by_role.add(instance_id)
    return len(activity_instances_instantiated_by_role)


def automated_activity_count(event_log: pd.DataFrame, case_id: str, automated_activities: set[str]) -> int:
    """
    The number of automated activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        automated_activities: The set of automated activities.

    """
    case_activities = cases_utils.act(event_log, case_id)
    return len(automated_activities.intersection(case_activities))


def automated_activity_instance_count(event_log: pd.DataFrame, case_id: str, automated_activities: set[str]) -> int:
    """
    The number of times that an automated activity is instantiated in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        automated_activities: The set of automated activities.

    """
    case_instances = cases_utils.inst(event_log, case_id)
    instances_of_automated_activities = set()
    for instance in case_instances:
        if instances_utils.act(event_log, instance) in automated_activities:
            instances_of_automated_activities.add(instance)
    return len(instances_of_automated_activities)


def desired_activity_count(event_log: pd.DataFrame, case_id: str, desired_activities: set[str]) -> int:
    """
    The number of instantiated activities whose occurence is desirable in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        desired_activities: The set of desired activities.

    """
    desired_activities = set(desired_activities)
    case_activities = cases_utils.act(event_log, case_id)
    return len(desired_activities.intersection(case_activities))


def human_resource_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of human resources that are involved in the execution of the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return len(cases_utils.hres(event_log, case_id))


def non_automated_activity_count(event_log: pd.DataFrame, case_id: str, automated_activities: set[str]) -> int:
    """
    The number of non-automated activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        automated_activities: The set of automated activities.

    """
    case_activities = cases_utils.act(event_log, case_id)
    return len(case_activities.difference(automated_activities))


def non_automated_activity_instance_count(event_log: pd.DataFrame, case_id: str, automated_activities: set[str]) -> int:
    """
    The number of times that an non-automated activity is instantiated in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        automated_activities: The set of automated activities.

    """
    non_automated_activity_instances = {
        instance
        for instance in cases_utils.inst(event_log, case_id)
        if instances_utils.act(event_log, instance) not in automated_activities
    }
    return len(non_automated_activity_instances)


def outcome_unit_count(event_log: pd.DataFrame, case_id: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    The outcome units associated with all instantiations of the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit calculations.

    """
    aggregation_function = {
        "sgl": quality_instances_indicators.outcome_unit_count_for_single_events_of_activity_instances,
        "sum": quality_instances_indicators.outcome_unit_count_for_sum_of_all_events_of_activity_instances,
    }
    case_instances = cases_utils.inst(event_log, case_id)

    outcome_unit_count: float = 0
    for instance_id in case_instances:
        outcome_unit = aggregation_function[aggregation_mode](event_log, instance_id)
        if outcome_unit is not None:
            outcome_unit_count += outcome_unit
    return outcome_unit_count


def overall_quality(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The overall quality associated with the outcome of the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    assert_column_exists(event_log, StandardColumnNames.QUALITY)
    case_rows = event_log[event_log[StandardColumnNames.CASE_ID] == case_id]
    return float(case_rows[StandardColumnNames.QUALITY].unique()[0])


def repeatability(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The inverted ratio between the number of activities that occur in the case, and the number of times that an activity has been instantiated in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return 1 - safe_division(
        general_cases_indicators.activity_count(event_log, case_id),
        general_cases_indicators.activity_instance_count(event_log, case_id),
    )


def rework_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of times that any activity has been instantiated again, after its first instantiation, in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    rework_count = 0

    for activity_name in event_log[StandardColumnNames.ACTIVITY].unique():
        rework_count += max(0, cases_activities_utils.count(event_log, case_id, activity_name) - 1)
    return rework_count


def rework_count_by_value(event_log: pd.DataFrame, case_id: str, value: float) -> int:
    """
    The number of times that the activity has been instantiated again, after it has been instantiated a certain number of times, in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        value: The certain number of times that the activity has been instantiated.

    """
    rework_count = 0

    for activity_name in event_log[StandardColumnNames.ACTIVITY].unique():
        rework_count += max(0, cases_activities_utils.count(event_log, case_id, activity_name) - value)
    return int(rework_count)


def rework_of_activities_subset(event_log: pd.DataFrame, case_id: str, activities_subset: set[str]) -> int:
    """
    The number of times that any activity belonging to a subset of activities has been instantiated again, after its first instantiation,
    in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        activities_subset: The subset of activities.

    """
    rework_count = 0

    for activity_name in activities_subset:
        rework_count += max(0, cases_activities_utils.count(event_log, case_id, activity_name) - 1)
    return rework_count


def rework_percentage(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The percentage of times that any activity has been instantiated again, after its first instantiation, in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    numerator = rework_count(event_log, case_id)
    denominator = general_cases_indicators.activity_instance_count(event_log, case_id)
    return safe_division(numerator, denominator)


def rework_percentage_by_value(event_log: pd.DataFrame, case_id: str, value: float) -> float:
    """
    The percentage of times that any activity has been instantiated again, after it has been instantiated a certain number of times, in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        value: The certain number of times that the activity has been instantiated.

    """
    numerator = rework_count_by_value(event_log, case_id, value)
    denominator = general_cases_indicators.activity_instance_count(event_log, case_id)
    return safe_division(numerator, denominator)


def rework_time(event_log: pd.DataFrame, case_id: str) -> pd.Timedelta:
    """
    The total elapsed time for all times that any activity has been instantiated again, after its first instantiation, in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    sum_of_first_occurrences_times = pd.Timedelta(0)
    for activity_name in event_log[StandardColumnNames.ACTIVITY].unique():
        sum_of_first_occurrences_times += cases_activities_utils.filt(event_log, case_id, activity_name)
    return time_cases_indicators.lead_time(event_log, case_id) - sum_of_first_occurrences_times


def successful_outcome_unit_count(
    event_log: pd.DataFrame, case_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> int:
    """
    The outcome units associated with all activity instances of the case, after deducting those that were unsuccessfully completed.

    Args:
        event_log: The event log.
        case_id: The case ID.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    sum_of_successful_outcome_unit_counts = 0
    for instance_id in cases_utils.inst(event_log, case_id):
        sum_of_successful_outcome_unit_counts += quality_instances_indicators.successful_outcome_unit_count(
            event_log, instance_id, aggregation_mode
        )
    return sum_of_successful_outcome_unit_counts


def successful_outcome_unit_percentage(
    event_log: pd.DataFrame, case_id: str, aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The percentage of outcome units associated with all activity instances of the case that were successfully completed.

    Args:
        event_log: The event log.
        case_id: The case ID.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    numerator = successful_outcome_unit_count(event_log, case_id, aggregation_mode)
    denominator = outcome_unit_count(event_log, case_id, aggregation_mode)
    return safe_division(numerator, denominator)


def unwanted_activity_count(event_log: pd.DataFrame, case_id: str, unwanted_activities: set[str]) -> int:
    """
    The number of unwanted activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        unwanted_activities: The set of unwanted activities names.

    """
    return len(unwanted_activities.intersection(cases_utils.act(event_log, case_id)))


def unwanted_activity_percentage(event_log: pd.DataFrame, case_id: str, unwanted_activities: set[str]) -> float:
    """
    The percentage of unwanted activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        unwanted_activities: The set of unwanted activities names.

    """
    numerator = unwanted_activity_count(event_log, case_id, unwanted_activities)
    denominator = general_cases_indicators.activity_count(event_log, case_id)
    return safe_division(numerator, denominator)


def unwanted_activity_instance_count(event_log: pd.DataFrame, case_id: str, unwanted_activities: set[str]) -> int:
    """
    The number of times that an unwanted activity is instantiated in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        unwanted_activities: The set of unwanted activities names.

    """
    unwanted_activity_instances = {
        instance
        for instance in cases_utils.inst(event_log, case_id)
        if instances_utils.act(event_log, instance) in unwanted_activities
    }
    return len(unwanted_activity_instances)


def unwanted_activity_instance_percentage(
    event_log: pd.DataFrame, case_id: str, unwanted_activities: set[str]
) -> float:
    """
    The percentage of times that an unwanted activity is instantiated in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        unwanted_activities: The set of unwanted activities names.

    """
    numerator = unwanted_activity_instance_count(event_log, case_id, unwanted_activities)
    denominator = general_cases_indicators.activity_instance_count(event_log, case_id)
    return safe_division(numerator, denominator)
