from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.general.groups as general_groups_indicators
import process_performance_indicators.indicators.time.cases as time_cases_indicators
import process_performance_indicators.utils.cases as cases_utils
import process_performance_indicators.utils.cases_activities as cases_activities_utils
from process_performance_indicators.exceptions import IndicatorDivisionError
from process_performance_indicators.utils.safe_division import safe_division


def expected_active_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The difference between the total elapsed time of a case belonging to the group of cases, and the
     sum of waiting times for every activity instance in a case belonging to the group of cases where
     no other activity instance was being executed.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    total_active_time: pd.Timedelta = pd.Timedelta(0)
    successful_cases = 0
    last_error: IndicatorDivisionError | None = None

    for case_id in case_ids:
        try:
            total_active_time += time_cases_indicators.active_time(event_log, case_id)
            successful_cases += 1
        except IndicatorDivisionError as e:  # noqa: PERF203
            last_error = e
            continue

    if len(case_ids) > 0 and successful_cases == 0 and last_error is not None:
        raise last_error

    return safe_division(total_active_time, successful_cases) if successful_cases > 0 else pd.Timedelta(0)


def activity_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    activities_in_group = set()
    for case in case_ids:
        activities_in_group.update(cases_utils.act(event_log, case))

    return len(activities_in_group)


def expected_activity_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    sum_of_activities_counts = 0
    for case_id in case_ids:
        sum_of_activities_counts += time_cases_indicators.activity_count(event_log, case_id)

    numerator = sum_of_activities_counts
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def activity_instance_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of times that any activity has been instantiated in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    count = 0
    for case_id in case_ids:
        count += time_cases_indicators.activity_instance_count(event_log, case_id)
    return count


def expected_activity_instance_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of times that any activity is instantiated in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    numerator = activity_instance_count(event_log, case_ids)
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
    for case in case_ids:
        activities_in_group.update(cases_utils.act(event_log, case))

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
    for case in case_ids:
        count += time_cases_indicators.automated_activity_count(event_log, case, automated_activities)

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
    for case in case_ids:
        count += time_cases_indicators.automated_activity_instance_count(event_log, case, automated_activities)
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


def automated_activity_service_time(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> pd.Timedelta:
    """
    The sum of elapsed times for all instantiations of automated activities in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    total_service_time: pd.Timedelta = pd.Timedelta(0)
    for case_id in case_ids:
        total_service_time += time_cases_indicators.automated_activity_service_time(
            event_log, case_id, automated_activities
        )
    return total_service_time


def expected_automated_activity_service_time(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], automated_activities: set[str]
) -> pd.Timedelta:
    """
    The expected sum of elapsed times for all instantiations of automated activities in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        automated_activities: The set of automated activities.

    """
    return safe_division(
        automated_activity_service_time(event_log, case_ids, automated_activities),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def case_count_lead_time_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the number of cases belonging to the group of cases, and the total elapsed time between the earliest
    and latest events in the group of cases. Returns cases per hour

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = general_groups_indicators.case_count(event_log, case_ids)
    # Using hour as the time unit for denominator
    denominator = lead_time(event_log, case_ids) / pd.Timedelta(hours=1)
    return safe_division(numerator, denominator)


def case_count_where_lead_time_over_value(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], lead_time_threshold: pd.Timedelta
) -> int:
    """
    The number of cases belonging to the group of cases whose total elapsed time between
    the earliest and latest events is greater than the given value.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        lead_time_threshold: The threshold value as a time delta.

    """
    cases_where_lead_time_over_value = {
        case_id for case_id in case_ids if time_cases_indicators.lead_time(event_log, case_id) > lead_time_threshold
    }
    return len(cases_where_lead_time_over_value)


def case_percentage_where_lead_time_over_value(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], lead_time_threshold: pd.Timedelta
) -> float:
    """
    The percentage of cases belonging to the group of cases whose total elapsed time between
    the earliest and latest events is greater than the given value.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        lead_time_threshold: The threshold value as a time delta.

    """
    numerator = case_count_where_lead_time_over_value(event_log, case_ids, lead_time_threshold)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_percentage_with_missed_deadline(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], deadline: pd.Timestamp
) -> float:
    """
    The percentage of cases belonging to the group of cases whose latest event occurs after a given deadline.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        deadline: The deadline value as a timestamp.

    """
    cases_over_deadline = {case_id for case_id in case_ids if cases_utils.endt(event_log, case_id) > deadline}
    numerator = len(cases_over_deadline)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_handover_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of times that a human resource associated with an activity instance
    differs from the human resource associated with the preceding activity instance
    within a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_handover_counts = 0
    for case_id in case_ids:
        sum_of_handover_counts += time_cases_indicators.handover_count(event_log, case_id)
    return safe_division(sum_of_handover_counts, general_groups_indicators.case_count(event_log, case_ids))


def expected_idle_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The expected sum of waiting times for every activity instance in a case belonging
    to the group of cases where no other activity instance was being executed.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    total_idle_time: pd.Timedelta = pd.Timedelta(0)
    successful_cases = 0
    last_error: IndicatorDivisionError | None = None

    for case_id in case_ids:
        try:
            total_idle_time += time_cases_indicators.idle_time(event_log, case_id)
            successful_cases += 1
        except IndicatorDivisionError as e:  # noqa: PERF203
            last_error = e
            continue

    if len(case_ids) > 0 and successful_cases == 0 and last_error is not None:
        raise last_error

    return safe_division(total_idle_time, successful_cases) if successful_cases > 0 else pd.Timedelta(0)


def lead_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The total elpased time between the earliest and latest eents in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    latest_end_time = max(cases_utils.endt(event_log, case_id) for case_id in case_ids)
    earliest_start_time = min(cases_utils.startt(event_log, case_id) for case_id in case_ids)
    return latest_end_time - earliest_start_time


def expected_lead_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The expected total elapsed time between the earliest and latest timestamps in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    group_total_lead_times_in_minutes = sum(
        time_cases_indicators.lead_time(event_log, case_id) / pd.Timedelta(minutes=1) for case_id in case_ids
    )
    case_count = general_groups_indicators.case_count(event_log, case_ids)
    expected_lead_time_in_minutes = safe_division(group_total_lead_times_in_minutes, case_count)
    return pd.Timedelta(minutes=expected_lead_time_in_minutes)


def lead_time_and_case_count_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The ratio between the total elapsed time between the earliest and latest events in the group of cases,
    and the number of cases belonging to the group of cases. Returns hours per case.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    group_lead_time_in_hours = lead_time(event_log, case_ids) / pd.Timedelta(hours=1)
    case_count = general_groups_indicators.case_count(event_log, case_ids)
    hours_per_case = safe_division(group_lead_time_in_hours, case_count)
    return pd.Timedelta(hours=hours_per_case)


def expected_lead_time_deviation_from_deadline(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], deadline_margin: pd.Timedelta
) -> pd.Timedelta:
    """
    The difference between the time that a case in the group of cases is expected to take,
    and the actual elapsed time between its earliest and latest timestamps.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        deadline_margin: The margin of error for the deadline.

    """
    # TODO: CHECK DEADLINE TYPE
    deviations_from_deadline_in_minutes = 0
    for case_id in case_ids:
        deviations_from_deadline_in_minutes += time_cases_indicators.lead_time_deviation_from_deadline(
            event_log, case_id, deadline_margin
        ) / pd.Timedelta(minutes=1)

    numerator = deviations_from_deadline_in_minutes
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    expected_deviation_from_deadline_in_minutes = safe_division(numerator, denominator)
    return pd.Timedelta(minutes=expected_deviation_from_deadline_in_minutes)


def expected_lead_time_deviation_from_expectation(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], expectation: pd.Timedelta
) -> pd.Timedelta:
    """
    The absolute value of the difference between the time that a case in the group of cases
    is expected to take, and the actual elapsed time between its earliest and latest timestamps.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        expectation: The time delta the case is expected to take.

    """
    deviations_from_expectation_in_minutes = 0
    for case_id in case_ids:
        deviations_from_expectation_in_minutes += time_cases_indicators.lead_time_deviation_from_expectation(
            event_log, case_id, expectation
        ) / pd.Timedelta(minutes=1)

    numerator = deviations_from_expectation_in_minutes
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    expected_deviation_from_expectation_in_minutes = safe_division(numerator, denominator)
    return pd.Timedelta(minutes=expected_deviation_from_expectation_in_minutes)


def expected_lead_time_from_activity_a(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activity_a: str
) -> pd.Timedelta:
    """
    The total elapsed time between the earliest instantiations of a specific activity, and
    the latest activity instance, that is expected for a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        activity_a: The specific activity name.

    """
    total_lead_time: pd.Timedelta = pd.Timedelta(0)
    for case_id in case_ids:
        lead_time = time_cases_indicators.lead_time_from_activity_a(event_log, case_id, activity_a)
        if lead_time is not None:
            total_lead_time += lead_time

    case_count = len({case_id for case_id in case_ids if cases_activities_utils.fi_s(event_log, case_id, activity_a)})

    return safe_division(total_lead_time, case_count)


def expected_lead_time_from_activity_a_to_b(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activity_a: str, activity_b: str
) -> pd.Timedelta:
    """
    The total elapsed time between the earliest instantiations of a specific activity, and the earliest
    instantiations of another specific activity that precedes the other, that is expected for a case
    belonging to the group of cases. Here "activity a precedes activity b".

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_a: The specific activity name that precedes activity b.
        activity_b: The specific activity name that follows activity a.

    """
    total_lead_time: pd.Timedelta = pd.Timedelta(0)

    for case_id in case_ids:
        lead_time = time_cases_indicators.lead_time_from_activity_a_to_b(event_log, case_id, activity_a, activity_b)
        if lead_time is not None:
            total_lead_time += lead_time

    case_count = len(
        {case_id for case_id in case_ids if cases_activities_utils.fi(event_log, case_id, activity_a, activity_b)}
    )
    return safe_division(total_lead_time, case_count)


def expected_lead_time_to_activity_a(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], activity_a: str
) -> pd.Timedelta:
    """
    The total elapsed time between the earliest activity instance, and the earliest instantiations of a
    specific activity , that is expected for a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_a: The specific activity name.

    """
    total_lead_time: pd.Timedelta = pd.Timedelta(0)
    for case_id in case_ids:
        lead_time = time_cases_indicators.lead_time_to_activity_a(event_log, case_id, activity_a)
        if lead_time is not None:
            total_lead_time += lead_time
    case_count = len({case_id for case_id in case_ids if cases_activities_utils.fi_c(event_log, case_id, activity_a)})
    return safe_division(total_lead_time, case_count)


def service_and_lead_time_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the sum of elapsed times between the start and complete events of all
    activity instances of the group of cases, and the total elapsed time between the earliest and latest
    events in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(service_time(event_log, case_ids), lead_time(event_log, case_ids))


def expected_service_and_lead_time_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the sum of elapsed times between the start and complete events of all activity instances
    of the group of cases, and the expected total elapsed time between the earliest and latest timestamps in a case
    belonging to the group of cases

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(service_time(event_log, case_ids), expected_lead_time(event_log, case_ids))


def service_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The sum of elapsed times between the start and complete events of all activity
    instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    sum_of_service_times_in_minutes = 0
    for case_id in case_ids:
        sum_of_service_times_in_minutes += time_cases_indicators.service_time(event_log, case_id) / pd.Timedelta(
            minutes=1
        )
    return pd.Timedelta(minutes=sum_of_service_times_in_minutes)


def expected_service_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The expected sum of elapsed times between the start and complete events of all activity
    instances of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    group_service_time_in_minutes = service_time(event_log, case_ids) / pd.Timedelta(minutes=1)
    case_count = general_groups_indicators.case_count(event_log, case_ids)
    expected_service_time_in_minutes = safe_division(group_service_time_in_minutes, case_count)
    return pd.Timedelta(minutes=expected_service_time_in_minutes)


def service_time_from_activity_a_to_b(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    activity_a: str,
    activity_b: str,
    time_aggregation_mode: Literal["s", "c", "sc", "w"],
) -> pd.Timedelta:
    """
    The sum of elapsed times between the start and complete events of all activity instances of every case in the group of cases,
    which occur between the earliest instantiations of a specific activity, and the earliest instantiations of another specific
    activity that precedes the other, in each case. Here "activity a precedes activity b".

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_a: The specific activity name that precedes activity b.
        activity_b: The specific activity name that follows activity a.
        time_aggregation_mode: The aggregation mode.
            "s": Considers activity instances that were started within the start and end activity instances.
            "c": Considers activity instances that were completed within the start and end activity instances.
            "sc": Considers activity instances that were either started or completed within the start and end activity instances.
            "w": Considers all activity instances that were active within the start and end activity instances.

    """
    sum_of_service_times: pd.Timedelta = pd.Timedelta(0)
    for case_id in case_ids:
        service_time = time_cases_indicators.service_time_from_activity_a_to_b(
            event_log, case_id, activity_a, activity_b, time_aggregation_mode
        )
        if service_time is not None:
            sum_of_service_times += service_time

    return sum_of_service_times


def expected_service_time_from_activity_a_to_b(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    activity_a: str,
    activity_b: str,
    time_aggregation_mode: Literal["s", "c", "sc", "w"],
) -> pd.Timedelta:
    """
    The expected sum of elapsed times between the start and complete events of all activity instances of every case in the group of cases,
    which occur between the earliest instantiations of a specific activity, and the earliest instantiations of another specific
    activity that precedes the other, in each case. Here "activity a precedes activity b".

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_a: The specific activity name that precedes activity b.
        activity_b: The specific activity name that follows activity a.
        time_aggregation_mode: The aggregation mode.
            "s": Considers activity instances that were started within the start and end activity instances.
            "c": Considers activity instances that were completed within the start and end activity instances.
            "sc": Considers activity instances that were either started or completed within the start and end activity instances.
            "w": Considers all activity instances that were active within the start and end activity instances.

    """
    cases_count = len(
        {case_id for case_id in case_ids if cases_activities_utils.fi(event_log, case_id, activity_a, activity_b)}
    )

    return safe_division(
        service_time_from_activity_a_to_b(event_log, case_ids, activity_a, activity_b, time_aggregation_mode),
        cases_count,
    )


def expected_waiting_time(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> pd.Timedelta:
    """
    The expected sum, for every activity instance in a case belonging to the group of cases, of the
    elapsed time between the complete event of the activity instance that precedes it, and its start event.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_waiting_times: pd.Timedelta = pd.Timedelta(0)
    for case_id in case_ids:
        sum_of_waiting_times += time_cases_indicators.waiting_time(event_log, case_id)
    return safe_division(sum_of_waiting_times, general_groups_indicators.case_count(event_log, case_ids))


def expected_waiting_time_from_activity_a_to_b(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    activity_a: str,
    activity_b: str,
    time_aggregation_mode: Literal["s", "c", "sc", "w"],
) -> pd.Timedelta:
    """
    The expected sum, for every activity instance in a case belonging to the group of cases, that occurs between the earliest
    instantiations of a specific activity, and the earliest instantiations of another specific activity
    that precedes the other, of the elapsed time between the complete event of the activity instance that precedes it,
    and its start event.

    Args:
        event_log: The event log.
        case_ids: The case IDs.
        activity_a: The specific activity name that precedes activity b.
        activity_b: The specific activity name that follows activity a.
        time_aggregation_mode: The aggregation mode.
            "s": Considers activity instances that were started within the start and end activity instances.
            "c": Considers activity instances that were completed within the start and end activity instances.
            "sc": Considers activity instances that were either started or completed within the start and end activity instances.
            "w": Considers all activity instances that were active within the start and end activity instances.

    """
    sum_of_waiting_times: pd.Timedelta = pd.Timedelta(0)
    for case_id in case_ids:
        waiting_time = time_cases_indicators.waiting_time_from_activity_a_to_b(
            event_log, case_id, activity_a, activity_b, time_aggregation_mode
        )
        if waiting_time is not None:
            sum_of_waiting_times += waiting_time

    case_counts = len(
        {case_id for case_id in case_ids if cases_activities_utils.fi(event_log, case_id, activity_a, activity_b)}
    )

    return safe_division(sum_of_waiting_times, case_counts)
