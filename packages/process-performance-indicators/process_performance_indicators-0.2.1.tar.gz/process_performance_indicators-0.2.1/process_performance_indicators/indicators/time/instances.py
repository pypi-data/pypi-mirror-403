import pandas as pd

import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.utils.safe_division import safe_division


def lead_time(event_log: pd.DataFrame, instance_id: str) -> pd.Timedelta:
    """
    The total elapsed time of the activity instance, measured as the sum of the elapsed time
    between the start and complete events of the activity instance, and the elapsed time between
    the complete event of the activity instance that precedes the current activity instance,
    and the start event of the current activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    return service_time(event_log, instance_id) + waiting_time(event_log, instance_id)


def service_and_lead_time_ratio(event_log: pd.DataFrame, instance_id: str) -> float:
    """
    The ratio between the elapsed time between the start and complete events of the activity instance,
    and the total elapsed time of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    return safe_division(service_time(event_log, instance_id), lead_time(event_log, instance_id))


def service_time(event_log: pd.DataFrame, instance_id: str) -> pd.Timedelta:
    """
    The elapsed time between the start and complete events of the activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    complete_time = instances_utils.ctime(event_log, instance_id)
    start_time = instances_utils.stime(event_log, instance_id)
    return complete_time - start_time


def waiting_time(event_log: pd.DataFrame, instance_id: str) -> pd.Timedelta:
    """
    The elapsed time between the complete event of the activity instance that
    precedes the current activity instance, and the start event of the current
    activity instance.

    Args:
        event_log: The event log.
        instance_id: The instance id.

    """
    prev_instances = instances_utils.prev_instances(event_log, instance_id)
    if not prev_instances:
        return pd.Timedelta(0)

    any_prev_instance_id = next(iter(prev_instances))
    return instances_utils.stime(event_log, instance_id) - instances_utils.ctime(event_log, any_prev_instance_id)
