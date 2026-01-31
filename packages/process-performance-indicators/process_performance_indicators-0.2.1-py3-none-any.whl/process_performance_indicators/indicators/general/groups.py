import pandas as pd

import process_performance_indicators.indicators.general.cases as general_cases_indicators
import process_performance_indicators.utils.cases as cases_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils.safe_division import safe_division


def activity_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    count = 0
    for case_id in case_ids:
        count += len(cases_utils.act(event_log, case_id))
    return count


def expected_activity_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    sum_of_activity_counts = 0
    for case_id in case_ids:
        sum_of_activity_counts += len(cases_utils.act(event_log, case_id))

    numerator = sum_of_activity_counts
    denominator = case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def activity_instance_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of times that any activity has been instantiated in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    count = 0
    for case_id in case_ids:
        count += general_cases_indicators.activity_instance_count(event_log, case_id)
    return count


def expected_activity_instance_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of times that any activity has been instantiated in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    sum_of_activity_instance_counts = 0
    for case_id in case_ids:
        sum_of_activity_instance_counts += general_cases_indicators.activity_instance_count(event_log, case_id)

    numerator = sum_of_activity_instance_counts
    denominator = case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def case_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of cases belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    event_log_unique_case_ids = set(event_log[StandardColumnNames.CASE_ID].unique())
    case_ids = set(case_ids)  # sanity check to ensure no duplicates if input is a list
    return len(case_ids.intersection(event_log_unique_case_ids))


def human_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of human resources that are involved in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    count = 0
    for case_id in case_ids:
        count += len(cases_utils.hres(event_log, case_id))
    return count


def expected_human_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of human resources that are involved in the execution of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    sum_of_human_resources_counts = 0
    for case_id in case_ids:
        sum_of_human_resources_counts += general_cases_indicators.human_resource_count(event_log, case_id)

    numerator = sum_of_human_resources_counts
    denominator = case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of resources that are involved in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    count = 0
    for case_id in case_ids:
        count += len(cases_utils.res(event_log, case_id))
    return count


def expected_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int | float:
    """
    The expected number of resources that are involved in the execution of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    sum_of_resource_counts = 0
    for case_id in case_ids:
        sum_of_resource_counts += general_cases_indicators.resource_count(event_log, case_id)

    numerator = sum_of_resource_counts
    denominator = case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def role_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of human resource roles that are involved in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    count = 0
    for case_id in case_ids:
        count += len(cases_utils.role(event_log, case_id))
    return count


def expected_role_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int | float:
    """
    The expected number of human resource roles that are involved in the execution of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The list or set of case ids.

    """
    _is_case_ids_empty(case_ids)
    sum_of_role_counts = 0
    for case_id in case_ids:
        sum_of_role_counts += general_cases_indicators.role_count(event_log, case_id)

    numerator = sum_of_role_counts
    denominator = case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def _is_case_ids_empty(case_ids: list[str] | set[str]) -> None:
    """
    Raises a ValueError if the case ids are empty.
    """
    if len(case_ids) == 0:
        raise ValueError("case_ids is empty. Please provide a valid list of case ids.")
