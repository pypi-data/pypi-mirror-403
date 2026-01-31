import pandas as pd

import process_performance_indicators.utils.activities as activities_utils


def activity_instance_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of times that a specific activity has been instantiated in the event log.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    return len(activities_utils.inst(event_log, activity_name))


def human_resource_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of human resources that are involved in the execution of the activity.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    return len(activities_utils.hres(event_log, activity_name))


def resource_count(event_log: pd.DataFrame, activity_name: str) -> int:
    """
    The number of resources that are involved in the execution of the activity.

    Args:
        event_log: The event log.
        activity_name: The name of the activity.

    """
    return len(activities_utils.res(event_log, activity_name))
