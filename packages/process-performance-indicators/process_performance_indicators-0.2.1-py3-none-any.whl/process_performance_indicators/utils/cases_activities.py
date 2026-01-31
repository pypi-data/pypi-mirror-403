from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.cost.instances as cost_instances_indicators
import process_performance_indicators.indicators.time.instances as time_instances_indicators
from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.exceptions import (
    ActivityNameNotFoundError,
    CaseIdNotFoundError,
)
from process_performance_indicators.utils import instances as instances_utils
from process_performance_indicators.utils.safe_division import safe_division


def inst(event_log: pd.DataFrame, case_id: str, activity_name: str) -> set[str]:
    """
    Returns the dataframe of instance of an activity in a case.
    """
    _is_case_id_activity_name_valid(event_log, case_id, activity_name)

    instances = event_log[
        (event_log[StandardColumnNames.CASE_ID] == case_id) & (event_log[StandardColumnNames.ACTIVITY] == activity_name)
    ][StandardColumnNames.INSTANCE]

    return set(instances.tolist())


def count(event_log: pd.DataFrame, case_id: str, activity_name: str) -> int:
    """
    Returns the number of times an activity occurs in a case.
    """
    return len(inst(event_log, case_id, activity_name))


def fi_s(event_log: pd.DataFrame, case_id: str, activity_name: str) -> set[str]:
    """
    Return the set of instance ids of activity `activity_name` in case `case_id`
    that start earliest (ties included).
    """
    _is_case_id_activity_name_valid(event_log, case_id, activity_name)
    instance_ids = inst(event_log, case_id, activity_name)

    if len(instance_ids) == 0:
        return set()

    instance_id_to_start_time = {iid: instances_utils.stime(event_log, iid) for iid in instance_ids}
    earliest_time = min(instance_id_to_start_time.values())
    return {iid for iid, t in instance_id_to_start_time.items() if t == earliest_time}


def fi_c(event_log: pd.DataFrame, case_id: str, activity_name: str) -> set[str]:
    """
    Return the set of instance ids of activity `activity_name` in case `case_id`
    that complete earliest (ties included).
    """
    _is_case_id_activity_name_valid(event_log, case_id, activity_name)
    instance_ids = inst(event_log, case_id, activity_name)

    if len(instance_ids) == 0:
        return set()

    instance_id_to_complete_time = {iid: instances_utils.ctime(event_log, iid) for iid in instance_ids}
    earliest_time = min(instance_id_to_complete_time.values())
    return {iid for iid, t in instance_id_to_complete_time.items() if t == earliest_time}


def fi(event_log: pd.DataFrame, case_id: str, activity_name_1: str, activity_name_2: str) -> set[str]:
    """
    Return the set of instance ids of activity `activity_name_2` in case `case_id`
    that start first after the earliest start of activity `activity_name_1` (ties included).
    """
    _is_case_id_activity_name_valid(event_log, case_id, activity_name_1)
    _is_case_id_activity_name_valid(event_log, case_id, activity_name_2)

    earliest_a_instance_ids = fi_s(event_log, case_id, activity_name_1)
    if len(earliest_a_instance_ids) == 0:
        return set()

    # Threshold is the (common) earliest start time of activity a (use max for safety if multiple equal)
    threshold_time = max(instances_utils.stime(event_log, iid) for iid in earliest_a_instance_ids)

    # Candidate b instances strictly after threshold
    b_instance_ids = inst(event_log, case_id, activity_name_2)
    b_after_threshold = {iid for iid in b_instance_ids if instances_utils.stime(event_log, iid) > threshold_time}
    if len(b_after_threshold) == 0:
        return set()

    # Among those, choose ones with minimal start time (no b in between)
    id_to_time = {iid: instances_utils.stime(event_log, iid) for iid in b_after_threshold}
    earliest_b_time = min(id_to_time.values())
    return {iid for iid, t in id_to_time.items() if t == earliest_b_time}


def fitc(event_log: pd.DataFrame, case_id: str, activity_name: str, aggregation_mode: Literal["sgl", "sum"]) -> float:
    """
    Returns the average cost of first occurences of activities in case `case_id`.
    """
    _is_case_id_activity_name_valid(event_log, case_id, activity_name)

    aggregation_functions = {
        "sgl": cost_instances_indicators.total_cost_for_single_events_of_activity_instances,
        "sum": cost_instances_indicators.total_cost_for_sum_of_all_events_of_activity_instances,
    }
    first_ocurrences = fi_s(event_log, case_id, activity_name)

    if len(first_ocurrences) == 0:
        return 0

    total_cost = 0
    for instance_id in first_ocurrences:
        cost = aggregation_functions[aggregation_mode](event_log, instance_id)
        total_cost += cost or 0  # TODO : ask if this approach is ok when total_cost is None

    return safe_division(total_cost, len(first_ocurrences))


def filt(event_log: pd.DataFrame, case_id: str, activity_name: str) -> pd.Timedelta:
    """
    Returns the average time of first occurrences of activities in case `case_id`.
    """
    first_occurrences = fi_s(event_log, case_id, activity_name)
    if not first_occurrences:
        return pd.Timedelta(0)

    sum_of_lead_times: pd.Timedelta = pd.Timedelta(0)
    for instance_id in first_occurrences:
        sum_of_lead_times += time_instances_indicators.lead_time(event_log, instance_id)

    return safe_division(sum_of_lead_times, len(first_occurrences))


def _is_case_id_activity_name_valid(event_log: pd.DataFrame, case_id: str, activity_name: str) -> None:
    """
    Checks if the case_id and activity_name are valid.
    Raises an exception if they are not valid.
    """
    is_case_id_valid = case_id in event_log[StandardColumnNames.CASE_ID].unique()
    is_activity_name_valid = activity_name in event_log[StandardColumnNames.ACTIVITY].unique()

    if not is_case_id_valid:
        raise CaseIdNotFoundError(f"Case ID {case_id} not found in event log.")
    if not is_activity_name_valid:
        raise ActivityNameNotFoundError(f"Activity name {activity_name} not found in event log.")
