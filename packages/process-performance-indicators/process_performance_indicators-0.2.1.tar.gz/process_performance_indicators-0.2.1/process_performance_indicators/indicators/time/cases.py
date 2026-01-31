from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.time.instances as time_instances_indicators
import process_performance_indicators.utils.cases as cases_utils
import process_performance_indicators.utils.cases_activities as cases_activities_utils
import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.exceptions import IndicatorDivisionError
from process_performance_indicators.utils.safe_division import safe_division


def active_time(event_log: pd.DataFrame, case_id: str) -> pd.Timedelta:
    """
    The difference between the total elapsed time of the case, and the sum of waiting
    times for every activity instance in the case where no other activity instance was being executed.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return lead_time(event_log, case_id) - idle_time(event_log, case_id)


def activity_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return len(cases_utils.act(event_log, case_id))


def activity_instance_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of times that any activity has been instantiated in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return len(cases_utils.inst(event_log, case_id))


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
        case_id: The case id.
        automated_activities: The set of automated activities.

    """
    case_instances = cases_utils.inst(event_log, case_id)
    instances_of_automated_activities = set()
    for instance in case_instances:
        if instances_utils.act(event_log, instance) in automated_activities:
            instances_of_automated_activities.add(instance)
    return len(instances_of_automated_activities)


def automated_activity_service_time(
    event_log: pd.DataFrame, case_id: str, automated_activities: set[str]
) -> pd.Timedelta:
    """
    The sum of elapsed times for all instantiations of automated activities in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.
        automated_activities: The set of automated activities.

    """
    total_service_time: pd.Timedelta = pd.Timedelta(0)
    for instance_id in cases_utils.inst(event_log, case_id):
        if instances_utils.act(event_log, instance_id) in automated_activities:
            total_service_time += time_instances_indicators.service_time(event_log, instance_id)
    return total_service_time


def handover_count(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The number of times that a human resource associated with an activity instance
    differs from the human resource associated with the preceding activity instance
    within the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    _handover_count = 0
    for instance_id in cases_utils.inst(event_log, case_id):
        _handover_count += instances_utils.dres(event_log, instance_id)
    return _handover_count


def idle_time(event_log: pd.DataFrame, case_id: str) -> pd.Timedelta:
    """
    The sum of waiting times for every activity instance in the case
    where no other activity instance was being executed.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    total_idle_time: pd.Timedelta = pd.Timedelta(0)
    eligible_instances = 0
    successful_calculations = 0
    last_error: IndicatorDivisionError | None = None

    for instance_id in cases_utils.inst(event_log, case_id):
        if not instances_utils.prev_instances(event_log, instance_id):
            continue

        eligible_instances += 1
        try:
            total_idle_time += safe_division(
                time_instances_indicators.waiting_time(event_log, instance_id),
                len(instances_utils.concstr(event_log, instance_id)),
            )
            successful_calculations += 1
        except IndicatorDivisionError as e:
            last_error = e
            continue

    if eligible_instances > 0 and successful_calculations == 0 and last_error is not None:
        raise last_error

    return total_idle_time


def lead_time(event_log: pd.DataFrame, case_id: str) -> pd.Timedelta:
    """
    The total elapsed time between the earliest and latest timestamps in the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    return cases_utils.endt(event_log, case_id) - cases_utils.startt(event_log, case_id)


def lead_time_deviation_from_deadline(
    event_log: pd.DataFrame, case_id: str, deadline_margin: pd.Timedelta
) -> pd.Timedelta:
    """
    The difference between the time that the case is expected to take, and the actual elapsed time between
    its earliest and latest timestamps. Negative values indicate that the case took less time than expected.

    Args:
        event_log: The event log.
        case_id: The case id.
        deadline_margin: The margin of error for the deadline.

    """
    # TODO: CHECK DEADLINE TYPE
    return deadline_margin - lead_time(event_log, case_id)


def lead_time_deviation_from_expectation(
    event_log: pd.DataFrame, case_id: str, expectation: pd.Timedelta
) -> pd.Timedelta:
    """
    The absolute value of the difference between the time that the case is expected to take,
    and the actual elapsed time between its earliest and latest timestamps.

    Args:
        event_log: The event log.
        case_id: The case id.
        expectation: The time delta the case is expected to take.

    """
    return abs(expectation - lead_time(event_log, case_id))


def lead_time_from_activity_a(event_log: pd.DataFrame, case_id: str, activity_a: str) -> pd.Timedelta | None:
    """
    The total elapsed time between the earliest instantiations of a specific activity, and
    the latest activity instance, in the case.

    Args:
        event_log: The event log.
        case_id: The case id.
        activity_a: The specific activity name.

    """
    instances_earliest_occurrences = cases_activities_utils.fi_s(event_log, case_id, activity_a)
    if not instances_earliest_occurrences:
        return None

    ending_instances = cases_utils.endin(event_log, case_id)

    any_earliest_instances = next(iter(instances_earliest_occurrences))
    any_ending_instances = next(iter(ending_instances))
    return instances_utils.lt(event_log, any_earliest_instances, any_ending_instances)


def lead_time_from_activity_a_to_b(
    event_log: pd.DataFrame, case_id: str, activity_a: str, activity_b: str
) -> pd.Timedelta | None:
    """
    The total elapsed time between the earliest instantiations of a specific activity, and the earliest
    instantiations of another specific activity that precedes the other, in the case. Here "activity a precedes activity b".

    Args:
        event_log: The event log.
        case_id: The case id.
        activity_a: The specific activity name that precedes activity b.
        activity_b: The specific activity name that follows activity a.

    """
    instances_earliest_ocurrences_after_other = cases_activities_utils.fi(event_log, case_id, activity_a, activity_b)
    if not instances_earliest_ocurrences_after_other:
        return None

    instances_earliest_occurrences = cases_activities_utils.fi_s(event_log, case_id, activity_a)

    any_earliest_instances = next(iter(instances_earliest_occurrences))  # x
    any_earliest_instances_after_other = next(iter(instances_earliest_ocurrences_after_other))  # y

    return instances_utils.lt(event_log, any_earliest_instances, any_earliest_instances_after_other)


def lead_time_to_activity_a(event_log: pd.DataFrame, case_id: str, activity_a: str) -> pd.Timedelta | None:
    """
    The total elapsed time between the earliest activity instance, and the earliest instantiations of a specific activity,
    in the case.

    Args:
        event_log: The event log.
        case_id: The case id.
        activity_a: The specific activity name.

    """
    instances_earliest_occurrences = cases_activities_utils.fi_c(event_log, case_id, activity_a)
    if not instances_earliest_occurrences:
        return None

    starting_instances = cases_utils.strin(event_log, case_id)

    any_starting_instances = next(iter(starting_instances))  # x
    any_earliest_instances = next(iter(instances_earliest_occurrences))  # y
    return instances_utils.lt(event_log, any_starting_instances, any_earliest_instances)


def service_and_lead_time_ratio(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The ratio between the sum of elapsed times between the start and complete events of
    all activity instance of the case, and the total elapsed time between the earliest and latest timestamps in the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    return safe_division(service_time(event_log, case_id), lead_time(event_log, case_id))


def service_time(event_log: pd.DataFrame, case_id: str) -> pd.Timedelta:
    """
    The sum of elapsed times between the start and complete events of all activity instances of the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    sum_of_service_times_in_minutes = 0
    for instance_id in cases_utils.inst(event_log, case_id):
        sum_of_service_times_in_minutes += time_instances_indicators.service_time(
            event_log, instance_id
        ) / pd.Timedelta(minutes=1)
    return pd.Timedelta(minutes=sum_of_service_times_in_minutes)


def service_time_from_activity_a_to_b(
    event_log: pd.DataFrame,
    case_id: str,
    activity_a: str,
    activity_b: str,
    time_aggregation_mode: Literal["s", "c", "sc", "w"],
) -> pd.Timedelta | None:
    """
    The sum elapsed times between the start and complete events of all activity instances of the case,
    which occur between the earliest instantiations of a specific activity, and the earliest instantiations
    of another specific activity that precedes the other. Here "activity a precedes activity b".

    Args:
        event_log: The event log.
        case_id: The case id.
        activity_a: The specific activity name that precedes activity b.
        activity_b: The specific activity name that follows activity a.
        time_aggregation_mode: The aggregation mode.
            "s": Considers activity instances that were started within the start and end activity instances.
            "c": Considers activity instances that were completed within the start and end activity instances.
            "sc": Considers activity instances that were either started or completed within the start and end activity instances.
            "w": Considers all activity instances that were active within the start and end activity instances.

    """
    instances_earliest_ocurrences_after_other = cases_activities_utils.fi(event_log, case_id, activity_a, activity_b)
    if not instances_earliest_ocurrences_after_other:
        return None

    instances_earliest_occurrences = cases_activities_utils.fi_s(event_log, case_id, activity_a)

    any_earliest_instances = next(iter(instances_earliest_occurrences))  # x
    any_earliest_instances_after_other = next(iter(instances_earliest_ocurrences_after_other))  # y

    return instances_utils.st(
        event_log, any_earliest_instances, any_earliest_instances_after_other, time_aggregation_mode
    )


def waiting_time(event_log: pd.DataFrame, case_id: str) -> pd.Timedelta:
    """
    The sum, for every activity instance in the case, of the elapsed time between
    the complete event of the activity instance that precedes it, and its start event.
    """
    sum_of_waiting_times: pd.Timedelta = pd.Timedelta(0)
    for instance_id in cases_utils.inst(event_log, case_id):
        sum_of_waiting_times += time_instances_indicators.waiting_time(event_log, instance_id)
    return sum_of_waiting_times


def waiting_time_from_activity_a_to_b(
    event_log: pd.DataFrame,
    case_id: str,
    activity_a: str,
    activity_b: str,
    time_aggregation_mode: Literal["s", "c", "sc", "w"],
) -> pd.Timedelta | None:
    """
    The sum, for every activity instance in the case that occurs between the earliest
    instantiations of a specific activity, and the earliest instantiations of another specific activity
    that precedes the other, of the elapsed time between the complete event of the activity instance that precedes it,
    and its start event.

    Args:
        event_log: The event log.
        case_id: The case id.
        activity_a: The specific activity name that precedes activity b.
        activity_b: The specific activity name that follows activity a.
        time_aggregation_mode: The aggregation mode.
            "s": Considers activity instances that were started within the start and end activity instances.
            "c": Considers activity instances that were completed within the start and end activity instances.
            "sc": Considers activity instances that were either started or completed within the start and end activity instances.
            "w": Considers all activity instances that were active within the start and end activity instances.

    """
    instances_earliest_ocurrences_after_other = cases_activities_utils.fi(event_log, case_id, activity_a, activity_b)
    if not instances_earliest_ocurrences_after_other:
        return None

    instances_earliest_occurrences = cases_activities_utils.fi_s(event_log, case_id, activity_a)

    any_earliest_instances = next(iter(instances_earliest_occurrences))  # x
    any_earliest_instances_after_other = next(iter(instances_earliest_ocurrences_after_other))  # y

    return instances_utils.wt(
        event_log, any_earliest_instances, any_earliest_instances_after_other, time_aggregation_mode
    )
