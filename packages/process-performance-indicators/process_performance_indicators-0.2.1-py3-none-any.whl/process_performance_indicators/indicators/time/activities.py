import pandas as pd

import process_performance_indicators.indicators.time.instances as time_instances_indicators
import process_performance_indicators.utils.activities as activities_utils
from process_performance_indicators.utils.safe_division import safe_division


def lead_time(event_log: pd.DataFrame, activity_name: str) -> pd.Timedelta:
    """
    The sum of total elapsed times of all instantiations of the activity.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    total_lead_time: pd.Timedelta = pd.Timedelta(0)
    for instance_id in activities_utils.inst(event_log, activity_name):
        total_lead_time += time_instances_indicators.lead_time(event_log, instance_id)
    return total_lead_time


def service_and_lead_time_ratio(event_log: pd.DataFrame, activity_name: str) -> float:
    """
    The ratio between the sum of elapsed times between the start and complete events of
    all instantiations of the activity, and the sum of total elapsed times for all instantiations
    of the activity.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    return safe_division(service_time(event_log, activity_name), lead_time(event_log, activity_name))


def service_time(event_log: pd.DataFrame, activity_name: str) -> pd.Timedelta:
    """
    The sum of elapsed times between the start and complete events of all instantiations of the activity

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    sum_of_service_times_in_minutes = 0
    for instance_id in activities_utils.inst(event_log, activity_name):
        sum_of_service_times_in_minutes += time_instances_indicators.service_time(
            event_log, instance_id
        ) / pd.Timedelta(minutes=1)
    return pd.Timedelta(minutes=sum_of_service_times_in_minutes)


def waiting_time(event_log: pd.DataFrame, activity_name: str) -> pd.Timedelta:
    """
    The sum of elapsed times between the complete events of activity instances that
    precede every instantiations of the activity, and the start event of each instantiation.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    sum_of_waiting_times: pd.Timedelta = pd.Timedelta(0)
    for instance_id in activities_utils.inst(event_log, activity_name):
        sum_of_waiting_times += time_instances_indicators.waiting_time(event_log, instance_id)
    return sum_of_waiting_times
