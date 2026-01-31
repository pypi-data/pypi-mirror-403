import pandas as pd

import process_performance_indicators.indicators.flexibility.cases as cases_flexibility_indicators
import process_performance_indicators.indicators.general.cases as general_cases_indicators
import process_performance_indicators.indicators.general.groups as general_groups_indicators
import process_performance_indicators.utils.cases as cases_utils
import process_performance_indicators.utils.groups as groups_utils
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.utils.column_validation import assert_column_exists
from process_performance_indicators.utils.safe_division import safe_division


def activity_and_role_count_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the number of activities that occur in the group of cases, and the number of human resources that are involved in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = general_groups_indicators.activity_count(event_log, case_ids)
    denominator = general_groups_indicators.role_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_activity_and_role_count_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the expected number of activities that occur in a case belonging to the group of cases, and the expected number of human resource roles that are involved in the execution of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_activities_count = 0
    sum_of_roles_count = 0
    for case_id in case_ids:
        sum_of_activities_count += general_cases_indicators.activity_count(event_log, case_id)
        sum_of_roles_count += general_cases_indicators.role_count(event_log, case_id)

    numerator = sum_of_activities_count
    denominator = sum_of_roles_count
    return safe_division(numerator, denominator)


def activity_instance_and_human_resource_count_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the number of times that any activity has been instantiated in the group of cases, and the number of human resources that are involved in the execution of cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = general_groups_indicators.activity_instance_count(event_log, case_ids)
    denominator = general_groups_indicators.human_resource_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_activity_instance_and_human_resource_count_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str]
) -> float:
    """
    The ratio between the expected number of times that any activity is instantiated in a case belonging to the group of cases, an the expected number of huma resources that are involed in the execution of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_human_resources_counts = 0
    for case_id in case_ids:
        sum_of_human_resources_counts += general_cases_indicators.human_resource_count(event_log, case_id)

    numerator = general_groups_indicators.activity_instance_count(event_log, case_ids)
    denominator = sum_of_human_resources_counts
    return safe_division(numerator, denominator)


def client_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of distinct clients associated with cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    assert_column_exists(event_log, StandardColumnNames.CLIENT)
    clients = set()
    for case_id in case_ids:
        clients.update(
            set(event_log[StandardColumnNames.CLIENT][event_log[StandardColumnNames.CASE_ID] == case_id].unique())
        )
    return len(clients)


def expected_client_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the number of distinct clients associated with cases in the group cases, and the number of cases belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = client_count(event_log, case_ids)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def directly_follows_relations_and_activity_count_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str]
) -> float:
    """
    The ratio between the number of activity pairs where one has been instantiated directly after the other in the group of cases, and the number of activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    return safe_division(
        directly_follows_relations_count(event_log, case_ids),
        general_groups_indicators.activity_count(event_log, case_ids),
    )


def expected_directly_follows_relations_and_activity_count_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str]
) -> float:
    """
    The ratio between the epected number of activity pairs where one has been instantiated directly after the other in a case belonging to the group of cases, and the expected number of activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_directly_follows_relations_counts = 0
    sum_of_activities_counts = 0
    for case_id in case_ids:
        sum_of_directly_follows_relations_counts += cases_flexibility_indicators.directly_follows_relations_count(
            event_log, case_id
        )
        sum_of_activities_counts += general_cases_indicators.activity_count(event_log, case_id)

    return safe_division(sum_of_directly_follows_relations_counts, sum_of_activities_counts)


def directly_follows_relations_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of activity pairs where one has been instantiated directly after the other in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    relations = set()
    for case_id in case_ids:
        relations.update(cases_utils.dfrel(event_log, case_id))
    return len(relations)


def expected_directly_follows_relations_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of activity pairs where one has been instantiated directly after the other in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_directly_follows_relations_counts = 0
    for case_id in case_ids:
        sum_of_directly_follows_relations_counts += cases_flexibility_indicators.directly_follows_relations_count(
            event_log, case_id
        )
    return safe_division(
        sum_of_directly_follows_relations_counts, general_groups_indicators.case_count(event_log, case_ids)
    )


def human_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of human resources that are involved in the execution of cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

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
        case_ids: The case IDs.

    """
    _is_case_ids_empty(case_ids)

    sum_of_human_resources_counts = 0
    for case_id in case_ids:
        sum_of_human_resources_counts += general_cases_indicators.human_resource_count(event_log, case_id)

    numerator = sum_of_human_resources_counts
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def optional_activity_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of optional activities that are instantiated in the group of cases. An activity is considered optional if there is at least one case in the event log where it does not occur.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    group_case_ids_log = event_log[event_log[StandardColumnNames.CASE_ID].isin(case_ids)]
    group_activities_per_case = (
        group_case_ids_log.groupby(StandardColumnNames.CASE_ID)[StandardColumnNames.ACTIVITY].apply(set).tolist()
    )
    group_unique_activities = set().union(*group_activities_per_case) if group_activities_per_case else set()

    other_cases = event_log[~event_log[StandardColumnNames.CASE_ID].isin(case_ids)]
    other_cases_activities = (
        other_cases.groupby(StandardColumnNames.CASE_ID)[StandardColumnNames.ACTIVITY].apply(set).tolist()
    )

    optional_activities = {
        activity
        for activity in group_unique_activities
        if any(activity not in activities for activities in other_cases_activities)
    }

    return len(optional_activities)


def expected_optional_activity_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of optional activities that are instantiated in a case belonging to the group of cases. An activity is considered optional if there is at least one case in the event log where it does not occur.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_optional_activities_counts = 0
    for case_id in case_ids:
        sum_of_optional_activities_counts += cases_flexibility_indicators.optional_activity_count(event_log, case_id)

    numerator = sum_of_optional_activities_counts
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def optionality(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the number of optional activities that are instantiated in the group of cases, and the number of activities that occur in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    numerator = optional_activity_count(event_log, case_ids)
    denominator = general_groups_indicators.activity_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def expected_optionality(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the expected number of optional activities that are instantiated in a case belonging to the group of cases, and the expected number of activities that occur in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    sum_of_optional_activities_counts = 0
    sum_of_activities_counts = 0
    for case_id in case_ids:
        sum_of_optional_activities_counts += cases_flexibility_indicators.optional_activity_count(event_log, case_id)
        sum_of_activities_counts += general_cases_indicators.activity_count(event_log, case_id)

    numerator = sum_of_optional_activities_counts
    denominator = sum_of_activities_counts
    return safe_division(numerator, denominator)


def role_and_variant_count_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The ratio between the number of human resource roles that are involved in the execution of the case, and the number of variants that are observed for the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    return safe_division(
        general_groups_indicators.role_count(event_log, case_ids),
        variant_count(event_log, case_ids),
    )


def role_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of human resource roles that are involed in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    _is_case_ids_empty(case_ids)
    count = 0
    for case_id in case_ids:
        count += len(cases_utils.role(event_log, case_id))
    return count


def expected_role_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of human resource roles that are involed in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    _is_case_ids_empty(case_ids)
    sum_of_role_counts = 0
    for case_id in case_ids:
        sum_of_role_counts += general_cases_indicators.role_count(event_log, case_id)
    numerator = sum_of_role_counts
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def variant_case_coverage(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The percentage of cases in the event log who possess the same variant as any case in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    group_variants = groups_utils.variants(event_log, case_ids)
    all_case_ids = set(event_log[StandardColumnNames.CASE_ID].unique())
    count = 0
    for c in all_case_ids:
        # if group_variants and c's trace have any common activities
        if group_variants.intersection(cases_utils.trace(event_log, c)):
            count += 1
    return safe_division(count, len(all_case_ids))


def variant_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of variants that are observed for the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case IDs.

    """
    return len(groups_utils.variants(event_log, case_ids))


def _is_case_ids_empty(case_ids: list[str] | set[str]) -> None:
    """
    Raises a ValueError if the case ids are empty.
    """
    if len(case_ids) == 0:
        raise ValueError("case_ids is empty. Please provide a valid list of case ids.")
