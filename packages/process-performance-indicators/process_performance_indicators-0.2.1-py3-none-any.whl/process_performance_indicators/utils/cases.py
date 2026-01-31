import itertools

import pandas as pd

import process_performance_indicators.utils.instances as instances_utils
from process_performance_indicators.constants import LifecycleTransitionType, StandardColumnNames
from process_performance_indicators.exceptions import (
    NoCompleteEventFoundError,
    NoStartEventFoundError,
)
from process_performance_indicators.utils import trace_cache
from process_performance_indicators.utils.column_validation import assert_column_exists


def events(event_log: pd.DataFrame, case_id: str) -> pd.DataFrame:
    """
    Get the events dataframe of a case.
    """
    _is_case_id_valid(event_log, case_id)

    return event_log[event_log[StandardColumnNames.CASE_ID] == case_id]


def act(event_log: pd.DataFrame, case_id: str) -> set[str]:
    """
    Get the activities names set of a case.
    """
    _is_case_id_valid(event_log, case_id)
    activities = event_log[event_log[StandardColumnNames.CASE_ID] == case_id][StandardColumnNames.ACTIVITY].unique()
    return set(activities)


def res(event_log: pd.DataFrame, case_id: str) -> set[str]:
    """
    Get the resources names set of a case.
    """
    _is_case_id_valid(event_log, case_id)
    assert_column_exists(event_log, StandardColumnNames.ORG_RESOURCE)

    resources = event_log[event_log[StandardColumnNames.CASE_ID] == case_id][StandardColumnNames.ORG_RESOURCE].unique()
    return set(resources)


def hres(event_log: pd.DataFrame, case_id: str) -> set[str]:
    """
    Get the human resources names set of a case.
    """
    _is_case_id_valid(event_log, case_id)
    assert_column_exists(event_log, StandardColumnNames.HUMAN_RESOURCE)

    human_resources = event_log[event_log[StandardColumnNames.CASE_ID] == case_id][
        StandardColumnNames.HUMAN_RESOURCE
    ].unique()
    return set(human_resources)


def role(event_log: pd.DataFrame, case_id: str) -> set[str]:
    """
    Get the roles names set of a case.
    """
    _is_case_id_valid(event_log, case_id)
    assert_column_exists(event_log, StandardColumnNames.ROLE)

    roles = event_log[event_log[StandardColumnNames.CASE_ID] == case_id][StandardColumnNames.ROLE].unique()
    return set(roles)


def inst(event_log: pd.DataFrame, case_id: str) -> set[str]:
    """
    Get the instances ids set of a case.
    """
    _is_case_id_valid(event_log, case_id)
    assert_column_exists(event_log, StandardColumnNames.INSTANCE)

    instances = event_log[event_log[StandardColumnNames.CASE_ID] == case_id][StandardColumnNames.INSTANCE].unique()
    return set(instances)


def strin(event_log: pd.DataFrame, case_id: str) -> set[str]:
    """
    Get the instance(s) that start first in the given case.
    """
    _is_case_id_valid(event_log, case_id)

    case_events = event_log[event_log[StandardColumnNames.CASE_ID] == case_id]
    start_events = case_events[case_events[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.START]

    min_start_time = start_events[StandardColumnNames.TIMESTAMP].min()
    earliest_instances = start_events[start_events[StandardColumnNames.TIMESTAMP] == min_start_time][
        StandardColumnNames.INSTANCE
    ].unique()
    return set(earliest_instances.tolist())


def endin(event_log: pd.DataFrame, case_id: str) -> set[str]:
    """
    Get the instance(s) that end last in the given case.
    """
    _is_case_id_valid(event_log, case_id)

    case_events = event_log[event_log[StandardColumnNames.CASE_ID] == case_id]
    complete_events = case_events[
        case_events[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.COMPLETE
    ]

    max_complete_time = complete_events[StandardColumnNames.TIMESTAMP].max()
    latest_instances = complete_events[complete_events[StandardColumnNames.TIMESTAMP] == max_complete_time][
        StandardColumnNames.INSTANCE
    ].unique()

    return set(latest_instances.tolist())


def startt(event_log: pd.DataFrame, case_id: str) -> pd.Timestamp:
    """
    Get the start timestamp of a case start activity instances
    """
    _is_case_id_valid(event_log, case_id)
    earliest_instances_events = strin(event_log, case_id)
    if not earliest_instances_events:
        raise NoStartEventFoundError(f"No start event found for case {case_id}.")
    col_timestamp: pd.Series[pd.Timestamp] = event_log[
        event_log[StandardColumnNames.INSTANCE].isin(earliest_instances_events)
    ][StandardColumnNames.TIMESTAMP]
    return col_timestamp.min()


def endt(event_log: pd.DataFrame, case_id: str) -> pd.Timestamp:
    """
    Get the end timestamp of a case end activity instances
    """
    _is_case_id_valid(event_log, case_id)
    latest_instances_events = endin(event_log, case_id)
    if not latest_instances_events:
        raise NoCompleteEventFoundError(f"No complete event found for case {case_id}.")
    col_timestamp: pd.Series[pd.Timestamp] = event_log[
        event_log[StandardColumnNames.INSTANCE].isin(latest_instances_events)
    ][StandardColumnNames.TIMESTAMP]
    return col_timestamp.max()


def dfrel(event_log: pd.DataFrame, case_id: str) -> set[tuple[str, str]]:
    """
    Returns a set of tuples, where each tuple contains the activity name of the directly-follows relation.
    """
    _is_case_id_valid(event_log, case_id)
    case_instances = inst(event_log, case_id)
    directly_follows_relations = set()

    for instance_i in case_instances:
        activity_i = instances_utils.act(event_log, instance_i)
        next_instances_of_i = instances_utils.next_instances(event_log, instance_i)

        for instance_i_prime in next_instances_of_i:
            activity_i_prime = instances_utils.act(event_log, instance_i_prime)
            directly_follows_relations.add((activity_i, activity_i_prime))

    return directly_follows_relations


def seq(event_log: pd.DataFrame, case_id: str) -> set[tuple[str, ...]]:
    """
    Returns a list of sequences, where each sequence is a list of instance IDs sorted by start time.
    When multiple instances have the same start time, multiple sequences are returned to represent
    all possible orderings of those concurrent instances.

    Example: If instances i1 and i2 start at the same time, followed by i3,
    returns [["i1", "i2", "i3"], ["i2", "i1", "i3"]]
    """
    # Check cache first
    cached_sequence = trace_cache.get_sequence(event_log, case_id)
    if cached_sequence is not None:
        return cached_sequence

    # Compute sequence
    case_instances = inst(event_log, case_id)

    if not case_instances:
        result = set()
        trace_cache.save_sequence(event_log, case_id, result)
        return result

    time_groups: dict[pd.Timestamp, list[str]] = {}
    for instance_id in case_instances:
        start_time = instances_utils.stime(event_log, instance_id)
        if start_time not in time_groups:
            time_groups[start_time] = []
        time_groups[start_time].append(instance_id)

    # Sort time groups by timestamp
    sorted_times = sorted(time_groups.keys())

    # Generate permutations for each time group of instances
    instance_group_permutations: list[list[list[str]]] = []
    for time in sorted_times:
        instance_group = time_groups[time]
        # Generate all permutations of concurrent instances
        permutations = list(itertools.permutations(instance_group))
        instance_group_permutations.append([list(perm) for perm in permutations])

    # Generate all possible sequences by taking cartesian product of permutation groups
    result = {
        tuple(instance for group in sequence_combination for instance in group)
        for sequence_combination in itertools.product(*instance_group_permutations)
    }

    # Save to cache
    trace_cache.save_sequence(event_log, case_id, result)
    return result


def trace(event_log: pd.DataFrame, case_id: str) -> set[tuple[str, ...]]:
    """
    Return all sequences of activity names for a case, mapped from instance sequences.
    Uses cached values if available, otherwise computes and caches.
    """
    # Check cache first
    cached_trace = trace_cache.get_trace(event_log, case_id)
    if cached_trace is not None:
        return cached_trace

    # Compute trace
    result = _compute_trace(event_log, case_id)

    # Save to cache
    trace_cache.save_trace(event_log, case_id, result)
    return result


def _compute_trace(event_log: pd.DataFrame, case_id: str) -> set[tuple[str, ...]]:
    """
    Internal function that computes the trace for a case.
    Maps instance sequences to activity name sequences.
    """
    sequences = seq(event_log, case_id)
    return {tuple(instances_utils.act(event_log, instance_id) for instance_id in sequence) for sequence in sequences}


def _is_case_id_valid(event_log: pd.DataFrame, case_id: str) -> None:
    """
    Raise an error if the case id is not found in the event log.

    Args:
        event_log: The event log.
        case_id: The case id of the corresponding case.

    Raises:
        ValueError: If the case id is not found in the event log.

    """
    if case_id == "" or case_id is None:
        raise ValueError("case_id is empty. Please provide a valid case id.")
    if case_id not in list(event_log[StandardColumnNames.CASE_ID].unique()):
        raise ValueError(
            f"CASE_ID = '{case_id}' not found in event log. Check your event log CASE_ID column for possible values."
        )
