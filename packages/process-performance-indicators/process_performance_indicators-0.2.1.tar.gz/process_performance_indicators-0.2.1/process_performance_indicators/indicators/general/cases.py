import pandas as pd

import process_performance_indicators.utils.cases as cases_utils


def activity_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    return len(cases_utils.act(event_log, case_id))


def activity_instance_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of times that any activity has been instantiated in the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    return len(cases_utils.inst(event_log, case_id))


def human_resource_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of human resources that are involved in the execution of the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    return len(cases_utils.hres(event_log, case_id))


def resource_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of resources that are involved in the execution of the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    return len(cases_utils.res(event_log, case_id))


def role_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of human resource roles that are involved in the execution of the case.

    Args:
        event_log: The event log.
        case_id: The case id.

    """
    return len(cases_utils.role(event_log, case_id))
