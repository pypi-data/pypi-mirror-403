from typing import Literal

import pandas as pd

from process_performance_indicators.constants import (
    LifecycleTransitionType,
    StandardColumnNames,
)
from process_performance_indicators.exceptions import (
    ColumnNotFoundError,
    InstanceIdNotFoundError,
)
from process_performance_indicators.utils import cases as cases_utils
from process_performance_indicators.utils.column_validation import assert_column_exists
from process_performance_indicators.utils.safe_division import safe_division


def start(event_log: pd.DataFrame, instance_id: str) -> pd.DataFrame:  # ignore: A001
    """
    Get the start event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    complete_event = cpl(event_log, instance_id)

    return _match(event_log, complete_event)


def cpl(event_log: pd.DataFrame, instance_id: str) -> pd.DataFrame:
    """
    Get the complete event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)

    return event_log[
        (event_log[StandardColumnNames.INSTANCE] == instance_id)
        & (event_log[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.COMPLETE)
    ]


def stime(event_log: pd.DataFrame, instance_id: str) -> pd.Timestamp:
    """
    Get the start time of an event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    start_event = start(event_log, instance_id)
    col: pd.Series[pd.Timestamp] = start_event[StandardColumnNames.TIMESTAMP]
    return col.iloc[0]


def ctime(event_log: pd.DataFrame, instance_id: str) -> pd.Timestamp:
    """
    Get the complete time of an event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    complete_event = cpl(event_log, instance_id)
    col: pd.Series[pd.Timestamp] = complete_event[StandardColumnNames.TIMESTAMP]
    return col.iloc[0]


def case(event_log: pd.DataFrame, instance_id: str) -> str:
    """
    Get the case of a complete event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    complete_event = cpl(event_log, instance_id)
    col: pd.Series[str] = complete_event[StandardColumnNames.CASE_ID]
    return col.iloc[0]


def act(event_log: pd.DataFrame, instance_id: str) -> str:
    """
    Get the activity of a complete event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    complete_event = cpl(event_log, instance_id)
    col: pd.Series[str] = complete_event[StandardColumnNames.ACTIVITY]
    return col.iloc[0]


def res(event_log: pd.DataFrame, instance_id: str) -> str:
    """
    Get the resource of a complete event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    assert_column_exists(event_log, StandardColumnNames.ORG_RESOURCE)

    complete_event = cpl(event_log, instance_id)
    col: pd.Series[str] = complete_event[StandardColumnNames.ORG_RESOURCE]
    return col.iloc[0]


def hres(event_log: pd.DataFrame, instance_id: str) -> str:
    """
    Get the human resource of a complete event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    assert_column_exists(event_log, StandardColumnNames.HUMAN_RESOURCE)

    complete_event = cpl(event_log, instance_id)
    col: pd.Series[str] = complete_event[StandardColumnNames.HUMAN_RESOURCE]
    return col.iloc[0]


def role(event_log: pd.DataFrame, instance_id: str) -> str:
    """
    Get the role of a complete event based on the instance id.
    """
    _is_instance_id_valid(event_log, instance_id)
    if StandardColumnNames.ROLE not in event_log.columns:
        error_message = "ROLE column not found in event log. Please ensure the event log contains the role column."
        raise ColumnNotFoundError(error_message)

    complete_event = cpl(event_log, instance_id)
    col: pd.Series[str] = complete_event[StandardColumnNames.ROLE]
    return col.iloc[0]


def prev_instances(event_log: pd.DataFrame, instance_id: str) -> set[str]:
    """
    Get the activity instances that occurred right before after activity instances.
    """
    _is_instance_id_valid(event_log, instance_id)
    start_time = stime(event_log, instance_id)
    case_id_val = case(event_log, instance_id)
    instance_ids = cases_utils.inst(event_log, case_id_val)
    completed_before: dict[str, pd.Timestamp] = {}
    for other in instance_ids:
        if other == instance_id:
            continue
        ct = ctime(event_log, other)
        if ct < start_time:
            completed_before[other] = ct
    if not completed_before:
        return set()
    latest_ct = max(completed_before.values())
    return {iid for iid, t in completed_before.items() if t == latest_ct}


def next_instances(event_log: pd.DataFrame, instance_id: str) -> set[str]:
    """
    Get the activity instances that occurred right after activity instances.
    """
    _is_instance_id_valid(event_log, instance_id)
    complete_time = ctime(event_log, instance_id)
    case_id_val = case(event_log, instance_id)
    instance_ids = cases_utils.inst(event_log, case_id_val)
    started_after: dict[str, pd.Timestamp] = {}
    for other in instance_ids:
        if other == instance_id:
            continue
        st = stime(event_log, other)
        if st > complete_time:
            started_after[other] = st
    if not started_after:
        return set()
    earliest_st = min(started_after.values())
    return {iid for iid, t in started_after.items() if t == earliest_st}


def prevstr(event_log: pd.DataFrame, instance_id: str) -> set[str]:
    """
    Get the activity instances that start before but finish after activity instances
    """
    _is_instance_id_valid(event_log, instance_id)
    instance_ids = cases_utils.inst(event_log, case(event_log, instance_id))
    prevstr_instances = set[str]()
    for other in instance_ids:
        if other == instance_id:
            continue
        if stime(event_log, other) < stime(event_log, instance_id) and ctime(event_log, other) > stime(
            event_log, instance_id
        ):
            prevstr_instances.add(other)
    return prevstr_instances


def concstr(event_log: pd.DataFrame, instance_id: str) -> set[str]:
    """
    Get the activity instances that start at the same time as activity instances
    """
    _is_instance_id_valid(event_log, instance_id)
    instance_ids = cases_utils.inst(event_log, case(event_log, instance_id))
    concurrent_instances = set[str]()
    for other in instance_ids:
        if stime(event_log, other) == stime(event_log, instance_id):
            concurrent_instances.add(other)
    return concurrent_instances


def dres(event_log: pd.DataFrame, instance_id: str) -> float:
    """
    Delegation of work for activity intances.
    If all activity instances that were completed right before the activity instances
    were associated with the same human resource as the activity instance, returns 0.
    If none of the activity instances that were complete right before the activity instance were
    associated with that human resource, returns 1.
    """
    _is_instance_id_valid(event_log, instance_id)
    previous_instances = prev_instances(event_log, instance_id)
    if not previous_instances:
        return 0

    instances_with_different_human_resource = 0
    for previous_instance in previous_instances:
        if hres(event_log, previous_instance) != hres(event_log, instance_id):
            instances_with_different_human_resource += 1

    return safe_division(instances_with_different_human_resource, len(previous_instances))


def instbetween_s(event_log: pd.DataFrame, instance_id_i: str, instance_id_prime: str) -> set[str]:
    """
    Get the activity instances that were started between two activity instances.
    """
    _is_instance_id_valid(event_log, instance_id_i)
    _is_instance_id_valid(event_log, instance_id_prime)

    instances = cases_utils.inst(event_log, case(event_log, instance_id_i))
    instbetween_s_instances = set[str]()

    start_time_i = stime(event_log, instance_id_i)
    complete_time_prime = ctime(event_log, instance_id_prime)

    for instance_double_prime in instances:
        if instance_double_prime in {instance_id_i, instance_id_prime}:
            continue

        start_time_double_prime = stime(event_log, instance_double_prime)

        if start_time_double_prime > start_time_i and start_time_double_prime < complete_time_prime:
            instbetween_s_instances.add(instance_double_prime)

    return instbetween_s_instances


def instbetween_c(event_log: pd.DataFrame, instance_id_i: str, instance_id_prime: str) -> set[str]:
    """
    Get the activity instances that were completed between two activity instances.
    """
    _is_instance_id_valid(event_log, instance_id_i)
    _is_instance_id_valid(event_log, instance_id_prime)

    instances = cases_utils.inst(event_log, case(event_log, instance_id_i))
    instbetween_c_instances = set[str]()

    start_time_i = stime(event_log, instance_id_i)
    complete_time_prime = ctime(event_log, instance_id_prime)

    for instance_double_prime in instances:
        if instance_double_prime in {instance_id_i, instance_id_prime}:
            continue

        complete_time_double_prime = ctime(event_log, instance_double_prime)

        if complete_time_double_prime > start_time_i and complete_time_prime > complete_time_double_prime:
            instbetween_c_instances.add(instance_double_prime)

    return instbetween_c_instances


def instbetween_sc(event_log: pd.DataFrame, instance_id_i: str, instance_id_prime: str) -> set[str]:
    """
    Get the activity instances that were either started or completed between two activity instances.
    """
    return instbetween_s(event_log, instance_id_i, instance_id_prime) | instbetween_c(
        event_log, instance_id_i, instance_id_prime
    )


def instbetween_w(event_log: pd.DataFrame, instance_id_i: str, instance_id_prime: str) -> set[str]:
    """
    Get the activity instances that were active between two activity instances
    """
    instances = cases_utils.inst(event_log, case(event_log, instance_id_i))
    active_instances = set[str]()

    start_time_i = stime(event_log, instance_id_i)
    complete_time_prime = ctime(event_log, instance_id_prime)

    for instance_double_prime in instances:
        if instance_double_prime in {instance_id_i, instance_id_prime}:
            continue

        start_time_double_prime = stime(event_log, instance_double_prime)
        complete_time_double_prime = ctime(event_log, instance_double_prime)

        if start_time_i > start_time_double_prime and complete_time_double_prime > complete_time_prime:
            active_instances.add(instance_double_prime)

    return instbetween_sc(event_log, instance_id_i, instance_id_prime) | active_instances


def timew(
    instance_x: pd.DataFrame,
    instance_x_prime: pd.DataFrame,
    instance_y: pd.DataFrame,
    instance_y_prime: pd.DataFrame,
) -> pd.Timedelta:
    """
    Time between pairs of activity instances
    """
    col_instance_x_time: pd.Series[pd.Timestamp] = instance_x[StandardColumnNames.TIMESTAMP]
    col_instance_x_prime_time: pd.Series[pd.Timestamp] = instance_x_prime[StandardColumnNames.TIMESTAMP]
    col_instance_y_time: pd.Series[pd.Timestamp] = instance_y[StandardColumnNames.TIMESTAMP]
    col_instance_y_prime_time: pd.Series[pd.Timestamp] = instance_y_prime[StandardColumnNames.TIMESTAMP]

    instance_x_time: pd.Timestamp = col_instance_x_time.iloc[0]
    instance_x_prime_time: pd.Timestamp = col_instance_x_prime_time.iloc[0]
    instance_y_time: pd.Timestamp = col_instance_y_time.iloc[0]
    instance_y_prime_time: pd.Timestamp = col_instance_y_prime_time.iloc[0]

    return min(instance_x_prime_time, instance_y_prime_time) - max(instance_x_time, instance_y_time)


def lt(event_log: pd.DataFrame, instance_id_i: str, instance_id_prime: str) -> pd.Timedelta:
    """
    Lead time between pairs of activity instances.
    """
    return ctime(event_log, instance_id_prime) - stime(event_log, instance_id_i)


def st(
    event_log: pd.DataFrame,
    instance_id_i: str,
    instance_id_prime: str,
    time_aggregation_mode: Literal["s", "c", "sc", "w"],
) -> pd.Timedelta:
    """
    Get the start time of an activity instance based on the aggregation mode.
    """
    if time_aggregation_mode not in {"s", "c", "sc", "w"}:
        raise ValueError(f"Invalid aggregation mode: {time_aggregation_mode}. Expected 's', 'c', 'sc', or 'w'.")

    instances_between_options = {
        "s": instbetween_s,
        "c": instbetween_c,
        "sc": instbetween_sc,
        "w": instbetween_w,
    }
    instances_between = instances_between_options[time_aggregation_mode](event_log, instance_id_i, instance_id_prime)

    time_between_instances: pd.Timedelta = pd.Timedelta(0)
    start_instance_i = start(event_log, instance_id_i)
    complete_instance_prime = cpl(event_log, instance_id_prime)

    for instance_double_prime in instances_between:
        start_instance_double_prime = start(event_log, instance_double_prime)
        complete_instance_double_prime = cpl(event_log, instance_double_prime)
        time_between_instances += timew(
            start_instance_i,
            complete_instance_prime,
            start_instance_double_prime,
            complete_instance_double_prime,
        )

    return time_between_instances


def wt(
    event_log: pd.DataFrame,
    instance_id_i: str,
    instance_id_prime: str,
    time_aggregation_mode: Literal["s", "c", "sc", "w"],
) -> pd.Timedelta:
    """
    Get the waiting time between pairs of activity instances
    """
    if time_aggregation_mode not in {"s", "c", "sc", "w"}:
        raise ValueError(f"Invalid aggregation mode: {time_aggregation_mode}. Expected 's', 'c', 'sc', or 'w'.")

    instances_between_options = {
        "s": instbetween_s,
        "c": instbetween_c,
        "sc": instbetween_sc,
        "w": instbetween_w,
    }
    instances_between = instances_between_options[time_aggregation_mode](event_log, instance_id_i, instance_id_prime)

    time_between_instances: pd.Timedelta = pd.Timedelta(0)
    start_instance_i = start(event_log, instance_id_i)
    complete_instance_prime = cpl(event_log, instance_id_prime)

    for instance_double_prime in instances_between:
        prev_instances_double_prime = prev_instances(event_log, instance_double_prime)
        if not prev_instances_double_prime:
            continue
        random_prev_instance = next(iter(prev_instances_double_prime))

        complete_instance_random_prev_instance = cpl(event_log, random_prev_instance)
        start_instance_double_prime = start(event_log, instance_double_prime)

        time_between_instances += timew(
            start_instance_i,
            complete_instance_prime,
            complete_instance_random_prev_instance,
            start_instance_double_prime,
        )
    return time_between_instances


def _is_instance_id_valid(event_log: pd.DataFrame, instance_id: str) -> None:
    """
    Check if the instance id is valid.

    Raises:
        InstanceIdNotFoundError: If the instance id is not found in the event log.

    """
    if instance_id not in event_log[StandardColumnNames.INSTANCE].unique():
        raise InstanceIdNotFoundError(f"Instance id {instance_id} not found in event log.")


def _match(event_log: pd.DataFrame, complete_event: pd.DataFrame) -> pd.DataFrame:
    """
    Match the event log to the instance id.
    """
    complete_event_instance_id: str = complete_event[StandardColumnNames.INSTANCE].unique()[0]

    start_event = event_log[
        (event_log[StandardColumnNames.INSTANCE] == complete_event_instance_id)
        & (event_log[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.START)
    ]
    if start_event.empty:
        return complete_event

    return start_event
