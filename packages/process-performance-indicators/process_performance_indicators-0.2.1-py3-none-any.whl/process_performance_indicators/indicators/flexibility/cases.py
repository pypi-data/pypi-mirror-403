import pandas as pd

import process_performance_indicators.indicators.general.cases as general_cases_indicators
import process_performance_indicators.utils.cases as cases_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils.safe_division import safe_division


def activity_and_role_count_ratio(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The ratio between the number of activities that occur in the case, and the number of human resources
    that are involved in the execution of the case

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    numerator = general_cases_indicators.activity_count(event_log, case_id)
    denominator = general_cases_indicators.role_count(event_log, case_id)
    return safe_division(numerator, denominator)


def activity_instance_and_human_resource_count_ratio(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The ratio between the number of times that any activity has been instantiated in the case, and the number of human resources that are involved in the execution of the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    numerator = general_cases_indicators.activity_instance_count(event_log, case_id)
    denominator = general_cases_indicators.human_resource_count(event_log, case_id)
    return safe_division(numerator, denominator)


def directly_follows_relations_and_activity_count_ratio(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The ratio between the number of activity pairs where one has been instantiated directly after the other in the case, and the number of activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return safe_division(
        directly_follows_relations_count(event_log, case_id),
        general_cases_indicators.activity_count(event_log, case_id),
    )


def directly_follows_relations_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of activity pairs where one has been instantiated directly after the other in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return len(cases_utils.dfrel(event_log, case_id))


def human_resource_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of human resources that are involved in the execution of the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return len(cases_utils.hres(event_log, case_id))


def optional_activity_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of optional activities that are instantiated in the case. An activity is considered optional if there is at least one case in the event log where it does not occur.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    target_activities = set(event_log[event_log[StandardColumnNames.CASE_ID] == case_id][StandardColumnNames.ACTIVITY])

    other_cases = event_log[event_log[StandardColumnNames.CASE_ID] != case_id]
    other_case_activities = (
        other_cases.groupby(StandardColumnNames.CASE_ID)[StandardColumnNames.ACTIVITY].apply(set).tolist()
    )

    optional_activities = {
        activity
        for activity in target_activities
        if any(activity not in activities for activities in other_case_activities)
    }

    return len(optional_activities)


def optionality(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The ratio between the number of optional activities that are instantiated in the case, and the number of activities that occur in the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    numerator = optional_activity_count(event_log, case_id)
    denominator = general_cases_indicators.activity_count(event_log, case_id)
    return safe_division(numerator, denominator)


def role_count(event_log: pd.DataFrame, case_id: str) -> int:
    """
    The number of human resource roles that are involved in the execution of the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    return len(cases_utils.role(event_log, case_id))


def variant_case_coverage(event_log: pd.DataFrame, case_id: str) -> float:
    """
    The percentage of cases in the event log who possess the same variant as the case.

    Args:
        event_log: The event log.
        case_id: The case ID.

    """
    case_traces = cases_utils.trace(event_log, case_id)
    all_case_ids = set(event_log[StandardColumnNames.CASE_ID].unique())
    count = 0

    for c_prime in all_case_ids:
        # if case_traces and c_prime's trace have any common activities
        if case_traces.intersection(cases_utils.trace(event_log, c_prime)):
            count += 1

    return safe_division(count, len(all_case_ids))
