from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.cost.groups as cost_groups_indicators
import process_performance_indicators.indicators.flexibility.groups as flexibility_groups_indicators
import process_performance_indicators.indicators.general.cases as general_cases_indicators
import process_performance_indicators.indicators.general.groups as general_groups_indicators
import process_performance_indicators.indicators.quality.cases as quality_cases_indicators
import process_performance_indicators.utils.cases as cases_utils
import process_performance_indicators.utils.cases_activities as cases_activities_utils
import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.utils.safe_division import safe_division


def activity_instance_count_by_human_resource(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], human_resource_name: str
) -> int:
    """
    The number of times that any activity is instantiated by a specific human resource in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        human_resource_name: The name of the human resource.

    """
    count = 0
    for case_id in case_ids:
        count += quality_cases_indicators.activity_instance_count_by_human_resource(
            event_log, case_id, human_resource_name
        )
    return count


def expected_activity_instance_count_by_human_resource(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], human_resource_name: str
) -> float:
    """
    The expected number of times that any activity is instantiated by a specific human resource in a case belonging to the group of cases

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        human_resource_name: The name of the human resource.

    """
    numerator = activity_instance_count_by_human_resource(event_log, case_ids, human_resource_name)
    denominator = general_groups_indicators.case_count(event_log, case_ids)

    return safe_division(numerator, denominator)


def activity_instance_count_by_role(event_log: pd.DataFrame, case_ids: list[str] | set[str], role_name: str) -> int:
    """
    The number of times that any activity is instantiated by a specific role in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        role_name: The name of the role.

    """
    count = 0
    for case_id in case_ids:
        count += quality_cases_indicators.activity_instance_count_by_role(event_log, case_id, role_name)
    return count


def expected_activity_instance_count_by_role(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], role_name: str
) -> int | float:
    """
    The expected number of times that any activity is instantiated by a specific role in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        role_name: The name of the role.

    """
    numerator = activity_instance_count_by_role(event_log, case_ids, role_name)
    denominator = general_groups_indicators.case_count(event_log, case_ids)

    return safe_division(numerator, denominator)


def automated_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> int:
    """
    The number of automated activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    activities_in_group = set()
    for case_id in case_ids:
        activities_in_group.update(cases_utils.act(event_log, case_id))

    return len(automated_activities.intersection(activities_in_group))


def expected_automated_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> float:
    """
    The expected number of automated activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    count = 0
    for case_id in case_ids:
        count += quality_cases_indicators.automated_activity_count(event_log, case_id, automated_activities)

    numerator = count
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def automated_activity_instance_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> int:
    """
    The number of times that an automated activity is instantiated in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    count = 0
    for case_id in case_ids:
        count += quality_cases_indicators.automated_activity_instance_count(event_log, case_id, automated_activities)
    return count


def expected_automated_activity_instance_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> float:
    """
    The expected number of times that an automated activity is instantiated in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    numerator = automated_activity_instance_count(event_log, case_ids, automated_activities)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_and_client_count_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the number of cases belonging to the group of cases, and the number of distinct clients associated with cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    return safe_division(
        general_groups_indicators.case_count(event_log, case_ids),
        flexibility_groups_indicators.client_count(event_log, case_ids),
    )


def case_count_where_activity_after_time_frame(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activity_name: str, end_time: pd.Timestamp
) -> int:
    """
    The number of cases belonging to the group of cases where a certain activity has occurred after a specific time frame.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_name: The name of the activity.
        end_time: The end time stamp.

    """
    resulting_cases = {
        case_id
        for case_id in case_ids
        if any(
            instances_utils.stime(event_log, instance) >= end_time
            for instance in cases_activities_utils.inst(event_log, case_id, activity_name)
        )
    }
    return len(resulting_cases)


def case_count_where_activity_before_time_frame(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activity_name: str, start_time: pd.Timestamp
) -> int:
    """
    The number of cases belonging to the group of cases where a certain activity has occurred before a specific time frame.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_name: The name of the activity.
        start_time: The start time stamp.

    """
    resulting_cases = {
        case_id
        for case_id in case_ids
        if any(
            instances_utils.stime(event_log, instance) <= start_time
            for instance in cases_activities_utils.inst(event_log, case_id, activity_name)
        )
    }
    return len(resulting_cases)


def case_count_where_activity_during_time_frame(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    activity_name: str,
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
) -> int:
    """
    The number of cases belonging to the group of cases where a certain activity has occurred within a specific time frame.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_name: The name of the activity.
        start_time: The start time.
        end_time: The end time.

    """
    resulting_cases = {
        case_id
        for case_id in case_ids
        if any(
            instances_utils.stime(event_log, instance) >= start_time
            and instances_utils.stime(event_log, instance) <= end_time
            for instance in cases_activities_utils.inst(event_log, case_id, activity_name)
        )
    }
    return len(resulting_cases)


def case_count_where_end_activity_is_a(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], a_activity_name: str
) -> int:
    """
    The number of cases belonging to the group of cases where a specific activity is the last instantiated one.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        a_activity_name: The name of the activity.

    """
    resulting_cases = {
        case_id
        for case_id in case_ids
        if any(
            instances_utils.act(event_log, instance_id) == a_activity_name
            for instance_id in cases_utils.endin(event_log, case_id)
        )
    }
    return len(resulting_cases)


def case_count_where_start_activity_is_a(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], a_activity_name: str
) -> int:
    """
    The number of cases belonging to the group of cases where a specific activity is the first instantiated one.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        a_activity_name: The name of the activity.

    """
    resulting_cases = {
        case_id
        for case_id in case_ids
        if any(
            instances_utils.act(event_log, instance_id) == a_activity_name
            for instance_id in cases_utils.strin(event_log, case_id)
        )
    }
    return len(resulting_cases)


def case_count_with_rework(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of cases belonging to the group of cases where there has been rework.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    resulting_cases = {case_id for case_id in case_ids if quality_cases_indicators.rework_count(event_log, case_id) > 0}
    return len(resulting_cases)


def case_percentage_where_activity_after_time_frame(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activity_name: str, end_time: pd.Timestamp
) -> float:
    """
    The percentage of cases belonging to the group of cases where a certain activity has occurred after a specific time frame.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_name: The name of the activity.
        end_time: The end time.

    """
    numerator = case_count_where_activity_after_time_frame(event_log, case_ids, activity_name, end_time)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_percentage_where_activity_before_time_frame(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activity_name: str, start_time: pd.Timestamp
) -> float:
    """
    The percentage of cases belonging to the group of cases where a certain activity has occurred before a specific time frame.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_name: The name of the activity.
        start_time: The start time.

    """
    numerator = case_count_where_activity_before_time_frame(event_log, case_ids, activity_name, start_time)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_percentage_where_activity_during_time_frame(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    activity_name: str,
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
) -> float:
    """
    The percentage of cases belonging to the group of cases where a certain activity has occurred within a specific time frame.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_name: The name of the activity.
        start_time: The start time.
        end_time: The end time.

    """
    numerator = case_count_where_activity_during_time_frame(event_log, case_ids, activity_name, start_time, end_time)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_percentage_where_end_activity_is_a(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], a_activity_name: str
) -> float:
    """
    The percentage of cases belonging to the group of cases where a specific activity is the last instantiated one.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        a_activity_name: The name of the activity.

    """
    numerator = case_count_where_end_activity_is_a(event_log, case_ids, a_activity_name)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_percentage_where_start_activity_is_a(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], a_activity_name: str
) -> float:
    """
    The percentage of cases belonging to the group of cases where a specific activity is the first instantiated one.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        a_activity_name: The name of the activity.

    """
    numerator = case_count_where_start_activity_is_a(event_log, case_ids, a_activity_name)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_percentage_with_missed_deadline(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], deadline: pd.Timestamp
) -> float:
    """
    The percentage of cases belonging to the group of cases whose latest event occurs after a given deadline.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        deadline: The deadline time stamp.

    """
    resulting_cases = {case_id for case_id in case_ids if cases_utils.endt(event_log, case_id) > deadline}
    return len(resulting_cases)


def case_percentage_with_rework(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The percentage of cases belonging to the group of cases where there has been rework.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = case_count_with_rework(event_log, case_ids)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def client_count_and_total_cost_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the number of distinct clients associated with cases in the group of cases,
    and the total cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = flexibility_groups_indicators.client_count(event_log, case_ids)
    denominator = cost_groups_indicators.total_cost(event_log, case_ids, aggregation_mode)
    return safe_division(numerator, denominator)


def expected_client_count_and_total_cost_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the number of distinct clients associated with cases in the group of cases,
    and the total cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = flexibility_groups_indicators.client_count(event_log, case_ids)
    denominator = cost_groups_indicators.total_cost(event_log, case_ids, aggregation_mode)
    return safe_division(numerator, denominator)


def desired_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], desired_activities: set[str]
) -> int:
    """
    The number of instantiated activities whose occurence is desirable in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        desired_activities: The set of desired activities.

    """
    activities_in_group = set()
    for case_id in case_ids:
        activities_in_group.update(cases_utils.act(event_log, case_id))

    return len(desired_activities.intersection(activities_in_group))


def expected_desired_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], desired_activities: set[str]
) -> float:
    """
    The expected number of instantiated activities whose occurrence is desirable in a case belonging to the groupd of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        desired_activities: The set of desired activities.

    """
    group_desired_activity_count = 0
    for case_id in case_ids:
        group_desired_activity_count += quality_cases_indicators.desired_activity_count(
            event_log, case_id, desired_activities
        )

    return safe_division(
        group_desired_activity_count, general_groups_indicators.activity_instance_count(event_log, case_ids)
    )


def human_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of human resources that are involved in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    cases_human_resources = set()
    for case_id in case_ids:
        cases_human_resources.update(cases_utils.hres(event_log, case_id))
    return len(cases_human_resources)


def expected_human_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int | float:
    """
    The expected number of human resources that are involved in the execution of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    human_resources_count = 0
    for case_id in case_ids:
        human_resources_count += quality_cases_indicators.human_resource_count(event_log, case_id)

    return safe_division(human_resources_count, general_groups_indicators.activity_instance_count(event_log, case_ids))


def non_automated_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> int:
    """
    The number of non-automated activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    activities_in_cases = set()
    for case_id in case_ids:
        activities_in_cases.update(cases_utils.act(event_log, case_id))

    return len(activities_in_cases.difference(automated_activities))


def expected_non_automated_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> float:
    """
    The expected number of non-automated activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    non_automated_activity_count = 0
    for case_id in case_ids:
        non_automated_activity_count += quality_cases_indicators.non_automated_activity_count(
            event_log, case_id, automated_activities
        )
    return safe_division(
        non_automated_activity_count, general_groups_indicators.activity_instance_count(event_log, case_ids)
    )


def non_automated_activity_instance_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> int:
    """
    The number of times that an non-automated activity is instantiated in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    non_automated_activity_instance_count = 0
    for case_id in case_ids:
        non_automated_activity_instance_count += quality_cases_indicators.non_automated_activity_instance_count(
            event_log, case_id, automated_activities
        )
    return non_automated_activity_instance_count


def expected_non_automated_activity_instance_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> float:
    """
    The expected number of times that an non-automated activity is instantiated in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    numerator = non_automated_activity_instance_count(event_log, case_ids, automated_activities)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def outcome_unit_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The outcome units associated with all instantiations of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit calculations.

    """
    outcome_unit_count = 0
    for case_id in case_ids:
        outcome_unit_count += quality_cases_indicators.outcome_unit_count(event_log, case_id, aggregation_mode)
    return outcome_unit_count


def expected_outcome_unit_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The expected outcome units associated with all activity instances of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.

    """
    numerator = outcome_unit_count(event_log, case_ids, aggregation_mode)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_overall_quality(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The overall quality associated with the outcome of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    cases_overall_quality = 0
    for case_id in case_ids:
        cases_overall_quality += quality_cases_indicators.overall_quality(event_log, case_id)

    numerator = cases_overall_quality
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def repeatability(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The inverted ratio between the number of activities that occur in the group of cases, and the number of times
    that an activity has been instantiated in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    return 1 - safe_division(
        general_groups_indicators.activity_count(event_log, case_ids),
        general_groups_indicators.activity_instance_count(event_log, case_ids),
    )


def expected_repeatability(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected inverted ratio between the number of activities that occur in a case belonging to the group of cases,
    and the number of times that an activity has been instantiated in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_activity_counts = 0

    for case_id in case_ids:
        sum_of_activity_counts += general_cases_indicators.activity_count(event_log, case_id)

    return 1 - safe_division(
        sum_of_activity_counts, general_groups_indicators.activity_instance_count(event_log, case_ids)
    )


def rework_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of times that any activity has been instantiated again, after its first instantiation, in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_rework_counts = 0
    for case_id in case_ids:
        sum_of_rework_counts += quality_cases_indicators.rework_count(event_log, case_id)
    return sum_of_rework_counts


def expected_rework_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int | float:
    """
    The expected number of times that any activity has been instantiated again, after its first instantiation, in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = rework_count(event_log, case_ids)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def rework_count_by_value(event_log: pd.DataFrame, case_ids: list[str] | set[str], value: float) -> int:
    """
    The number of times that the activity has been instantiated again, after it has been instantiated a certain number of times, in every case of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        value: The certain number of times that the activity has been instantiated.

    """
    sum_of_rework_counts = 0
    for case_id in case_ids:
        sum_of_rework_counts += quality_cases_indicators.rework_count_by_value(event_log, case_id, value)
    return sum_of_rework_counts


def expected_rework_count_by_value(event_log: pd.DataFrame, case_ids: list[str] | set[str], value: float) -> float:
    """
    The expected number of times that the activity has been instantiated again, after it has been instantiated a certain number of times,
    in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        value: The certain number of times that the activity has been instantiated.

    """
    numerator = rework_count_by_value(event_log, case_ids, value)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def rework_of_activities_subset(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activities_subset: set[str]
) -> int:
    """
    The number of times that any activity belonging to a subset of activities has been instantiated again, after its first instantiation,
    in every case of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activities_subset: The subset of activities.

    """
    sum_of_rework_counts = 0
    for case_id in case_ids:
        sum_of_rework_counts += quality_cases_indicators.rework_of_activities_subset(
            event_log, case_id, activities_subset
        )
    return sum_of_rework_counts


def expected_rework_of_activities_subset(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activities_subset: set[str]
) -> float:
    """
    The expected number of times that any activity belonging to a subset of activities has been instantiated again, after its first instantiation,
    in a case belonging to the group of cases.

    """
    numerator = rework_of_activities_subset(event_log, case_ids, activities_subset)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def rework_percentage(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The percentage of times that any activity has been instantiated again, after its first instantiation,
    in every case of the group of cases.


    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = rework_count(event_log, case_ids)
    denominator = general_groups_indicators.activity_instance_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_rework_percentage(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected percentage of times that any activity has been instantiated again, after its first instantiation,
    in a case belonging to the group of cases.


    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_rework_percentages = 0
    for case_id in case_ids:
        sum_of_rework_percentages += quality_cases_indicators.rework_percentage(event_log, case_id)

    numerator = sum_of_rework_percentages
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def rework_percentage_by_value(event_log: pd.DataFrame, case_ids: list[str] | set[str], value: float) -> float:
    """
    The percentage of times that any activity has been instantiated again, after it has been instantiated a certain number of times,
    in every case of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        value: The certain number of times that the activity has been instantiated.

    """
    numerator = rework_count_by_value(event_log, case_ids, value)
    denominator = general_groups_indicators.activity_instance_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_rework_percentage_by_value(event_log: pd.DataFrame, case_ids: list[str] | set[str], value: float) -> float:
    """
    The expected percentage of times that any activity has been instantiated again, after it has been instantiated a certain number of times, in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        value: The certain number of times that the activity has been instantiated.

    """
    sum_of_rework_by_value_percentages = 0
    for case_id in case_ids:
        sum_of_rework_by_value_percentages += quality_cases_indicators.rework_percentage_by_value(
            event_log, case_id, value
        )

    numerator = sum_of_rework_by_value_percentages
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def rework_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The total elapsed time for all times that any activity has been instantiated again, after its first instantiation,
    in every case of group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_rework_times = pd.Timedelta(0)
    for case_id in case_ids:
        sum_of_rework_times += quality_cases_indicators.rework_time(event_log, case_id)
    return sum_of_rework_times


def expected_rework_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The expected total elapsed time for all times that any activity has been instantiated again, after its first instantiation,
    in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    return safe_division(rework_time(event_log, case_ids), general_groups_indicators.case_count(event_log, case_ids))


def successful_outcome_unit_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> int:
    """
    The outcome units associated with all activity instances of the group of cases, after deducting those that were unsuccessfully completed.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    sum_of_successful_outcome_unit_counts = 0
    for case_id in case_ids:
        sum_of_successful_outcome_unit_counts += quality_cases_indicators.successful_outcome_unit_count(
            event_log, case_id, aggregation_mode
        )
    return sum_of_successful_outcome_unit_counts


def expected_successful_outcome_unit_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> int | float:
    """
    The expected outcome units associated with all activity instances of a case belonging to the group of cases, after deducting those that were unsuccessfully completed.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.


    """
    numerator = successful_outcome_unit_count(event_log, case_ids, aggregation_mode)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def successful_outcome_unit_percentage(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The percentage of outcome units associated with all activity instances of the group of cases that were successfully completed.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    numerator = successful_outcome_unit_count(event_log, case_ids, aggregation_mode)
    denominator = outcome_unit_count(event_log, case_ids, aggregation_mode)
    return safe_division(numerator, denominator)


def expected_successful_outcome_unit_percentage(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The expected percentage of outcome units associated with all activity instances of a case belonging to the group of cases that were successfully completed.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for outcome unit count calculations.
            "sum": Considers the sum of all events of activity instances for outcome unit count calculations.

    """
    sum_of_successful_outcome_unit_percentages = 0
    for case_id in case_ids:
        sum_of_successful_outcome_unit_percentages += quality_cases_indicators.successful_outcome_unit_percentage(
            event_log, case_id, aggregation_mode
        )

    numerator = sum_of_successful_outcome_unit_percentages
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def total_cost_and_client_count_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all activity instances of the group of cases, and the number of distinct clients associated with cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = flexibility_groups_indicators.client_count(event_log, case_ids)
    denominator = cost_groups_indicators.total_cost(event_log, case_ids, aggregation_mode)
    return safe_division(numerator, denominator)


def expected_total_cost_and_client_count_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The expected ratio between the total cost associated with all activity instances of the group of cases, and the number of distinct clients associated with cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = flexibility_groups_indicators.client_count(event_log, case_ids)
    denominator = cost_groups_indicators.total_cost(event_log, case_ids, aggregation_mode)
    return safe_division(numerator, denominator)


def unwanted_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> int:
    """
    The number of unwanted activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    activities_in_group = set()
    for case_id in case_ids:
        activities_in_group.update(cases_utils.act(event_log, case_id))

    return len(unwanted_activities.intersection(activities_in_group))


def expected_unwanted_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> int:
    """
    The expected number of unwanted activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    sum_of_unwanted_activity_counts = 0
    for case_id in case_ids:
        sum_of_unwanted_activity_counts += quality_cases_indicators.unwanted_activity_count(
            event_log, case_id, unwanted_activities
        )
    return sum_of_unwanted_activity_counts


def unwanted_activity_percentage(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> float:
    """
    The percentage of unwanted activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    numerator = unwanted_activity_count(event_log, case_ids, unwanted_activities)
    denominator = general_groups_indicators.activity_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_unwanted_activity_percentage(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> float:
    """
    The expected percentage of unwanted activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    sum_of_unwanted_activity_percentages = 0
    for case_id in case_ids:
        sum_of_unwanted_activity_percentages += quality_cases_indicators.unwanted_activity_percentage(
            event_log, case_id, unwanted_activities
        )

    numerator = sum_of_unwanted_activity_percentages
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def unwanted_activity_instance_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> int:
    """
    The number of times that an unwanted activity is instantiated in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    sum_of_unwanted_activity_instance_counts = 0
    for case_id in case_ids:
        sum_of_unwanted_activity_instance_counts += quality_cases_indicators.unwanted_activity_instance_count(
            event_log, case_id, unwanted_activities
        )
    return sum_of_unwanted_activity_instance_counts


def expected_unwanted_activity_instance_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> float:
    """
    The expected number of times that an unwanted activity is instantiated in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    numerator = unwanted_activity_instance_count(event_log, case_ids, unwanted_activities)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def unwanted_activity_instance_percentage(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> float:
    """
    The percentage of times that an unwanted activity is instantiated in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    numerator = unwanted_activity_instance_count(event_log, case_ids, unwanted_activities)
    denominator = general_groups_indicators.activity_instance_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_unwanted_activity_instance_percentage(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], unwanted_activities: set[str]
) -> float:
    """
    The expected percentage of times that an unwanted activity is instantiated in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        unwanted_activities: The set of unwanted activities names.

    """
    sum_of_unwanted_activity_instance_percentages = 0
    for case_id in case_ids:
        sum_of_unwanted_activity_instance_percentages += quality_cases_indicators.unwanted_activity_instance_percentage(
            event_log, case_id, unwanted_activities
        )

    numerator = sum_of_unwanted_activity_instance_percentages
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)
