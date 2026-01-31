from enum import Enum, auto

import pandas as pd

from process_performance_indicators.constants import (
    LifecycleTransitionType,
    StandardColumnNames,
)
from process_performance_indicators.formatting.column_mapping import (
    StandardColumnMapping,
    convert_to_standard_mapping,
    validate_column_mapping,
)
from process_performance_indicators.formatting.conversions import convert_to_explicit_interval_log


class EventLogType(Enum):
    """Enum representing the different types of event logs."""

    ATOMIC = auto()  # No lifecycle, no start_timestamp, no instance
    DERIVABLE_INTERVAL = auto()  # Has lifecycle, no instance
    PRODUCTION_STYLE = auto()  # Has start_timestamp, no lifecycle
    EXPLICIT_INTERVAL = auto()  # Has lifecycle AND instance


def event_log_formatter(
    event_log: pd.DataFrame,
    column_mapping: StandardColumnMapping,
    date_format: str | None = None,
    *,
    dayfirst: bool = False,
) -> pd.DataFrame:
    """
    Format an event log into a pandas DataFrame with standardized column names
    and return an explicit interval log with instance IDs assigned.

    Handles four types of event logs:

    1. Atomic logs (no lifecycle, no start_timestamp, no instance):
       - Each row is an instantaneous event
       - Duplicates each row with start and complete events (same timestamp)
       - Matches pairs to assign instance IDs

    2. Derivable interval logs (has lifecycle, no instance):
       - Already has start/complete events
       - Uses matching to assign instance IDs to start/complete pairs

    3. Production-style logs (has start_timestamp, no lifecycle):
       - Each row has start_timestamp and timestamp (end)
       - Splits into start and complete events
       - Matches pairs to assign instance IDs

    4. Explicit interval logs (has lifecycle AND instance):
       - Already has all required information
       - Only renames columns and converts types

    Args:
        event_log: The event log to format.
        column_mapping: The column mapping to use.
        date_format: The datetime format to use when parsing timestamp columns.
                    Can be a specific format string (e.g., "%d-%m-%Y %H:%M:%S"),
                    "ISO8601" for ISO8601 format, "mixed" for automatic inference,
                    or None to use pandas default parsing.
        dayfirst: Whether to interpret the first value in an ambiguous date
                 (e.g., 01/05/09) as the day (True) or month (False).
                 Only used when date_format is None or "mixed".

    Returns:
        pd.DataFrame: An explicit interval log with instance IDs and lifecycle transitions.

    """
    event_log = event_log.copy()

    # Standardize columns and convert types
    standard_named_log = _standardize_columns(event_log, column_mapping)
    _convert_standard_types(standard_named_log)

    # Detect log type and process accordingly
    log_type = _detect_log_type(column_mapping)

    if log_type == EventLogType.EXPLICIT_INTERVAL:
        return _process_explicit_interval_log(standard_named_log, date_format, dayfirst=dayfirst)

    if log_type == EventLogType.DERIVABLE_INTERVAL:
        return _process_derivable_interval_log(standard_named_log, date_format, dayfirst=dayfirst)

    if log_type == EventLogType.PRODUCTION_STYLE:
        return _process_production_style_log(standard_named_log, date_format, dayfirst=dayfirst)

    return _process_atomic_log(standard_named_log, date_format, dayfirst=dayfirst)


def _detect_log_type(column_mapping: StandardColumnMapping) -> EventLogType:
    """
    Detect the type of event log based on the column mapping.

    Args:
        column_mapping: The column mapping configuration.

    Returns:
        EventLogType: The detected log type.

    Detection logic:
        - If lifecycle_type_key AND instance_key provided --> Explicit interval
        - If lifecycle_type_key provided but NOT instance_key --> Derivable interval
        - If start_timestamp_key provided (no lifecycle_type_key) --> Production-style
        - None of above --> Atomic log

    """
    has_lifecycle = column_mapping.lifecycle_type_key is not None
    has_instance = column_mapping.instance_key is not None
    has_start_timestamp = column_mapping.start_timestamp_key is not None

    if has_lifecycle and has_instance:
        return EventLogType.EXPLICIT_INTERVAL
    if has_lifecycle and not has_instance:
        return EventLogType.DERIVABLE_INTERVAL
    if has_start_timestamp and not has_lifecycle:
        return EventLogType.PRODUCTION_STYLE
    return EventLogType.ATOMIC


def _convert_timestamp_column(
    log_df: pd.DataFrame,
    column_name: str,
    date_format: str | None,
    *,
    dayfirst: bool,
) -> None:
    """
    Convert a timestamp column to datetime in place.

    Timestamps are always converted to timezone-naive datetimes. If the source data
    contains timezone-aware timestamps, they are first converted to UTC and then
    the timezone info is stripped.

    Args:
        log_df: The DataFrame containing the column.
        column_name: The name of the column to convert.
        date_format: The datetime format to use.
        dayfirst: Whether to interpret ambiguous dates as day-first.

    """
    if date_format is not None:
        log_df[column_name] = pd.to_datetime(log_df[column_name], format=date_format)
    else:
        log_df[column_name] = pd.to_datetime(log_df[column_name], dayfirst=dayfirst)

    # Strip timezone info to ensure all timestamps are naive
    # This allows consistent comparison with user-provided naive timestamps
    if log_df[column_name].dt.tz is not None:
        log_df[column_name] = log_df[column_name].dt.tz_convert("UTC").dt.tz_localize(None)


def _standardize_columns(
    event_log: pd.DataFrame,
    column_mapping: StandardColumnMapping,
) -> pd.DataFrame:
    """
    Rename columns to standard names and filter to only mapped columns.

    Args:
        event_log: The event log to standardize.
        column_mapping: The column mapping to use.

    Returns:
        pd.DataFrame: The standardized event log.

    """
    standard_mapping = convert_to_standard_mapping(column_mapping)
    validate_column_mapping(standard_mapping, set(event_log.columns))

    inverted_mapping = {v: k for k, v in standard_mapping.items()}

    columns_to_keep = list(inverted_mapping.keys())
    filtered_log = event_log[columns_to_keep]

    return filtered_log.rename(columns=inverted_mapping)


def _convert_standard_types(log_df: pd.DataFrame) -> None:
    """
    Convert standard columns to their expected types in place.

    Args:
        log_df: The DataFrame to convert.

    """
    # Convert case id to string
    log_df[StandardColumnNames.CASE_ID] = log_df[StandardColumnNames.CASE_ID].astype(str)

    # Convert activity name to string
    log_df[StandardColumnNames.ACTIVITY] = log_df[StandardColumnNames.ACTIVITY].astype(str)

    # Convert instance to string if present
    if StandardColumnNames.INSTANCE in log_df.columns:
        log_df[StandardColumnNames.INSTANCE] = log_df[StandardColumnNames.INSTANCE].astype(str)


def _process_atomic_log(
    log_df: pd.DataFrame,
    date_format: str | None,
    *,
    dayfirst: bool,
) -> pd.DataFrame:
    """
    Process an atomic event log.

    Atomic logs have only case_id, activity, and timestamp.
    Each row represents an instantaneous event where start and complete are the same.

    Processing:
        1. Mark all rows as complete events
        2. Duplicate each row with start event type (same timestamp)
        3. Match start/complete pairs to assign instance IDs

    Args:
        log_df: The standardized event log.
        date_format: The datetime format.
        dayfirst: Whether to interpret ambiguous dates as day-first.

    Returns:
        pd.DataFrame: An explicit interval log.

    """
    # Convert timestamp to datetime
    _convert_timestamp_column(log_df, StandardColumnNames.TIMESTAMP, date_format, dayfirst=dayfirst)

    # Create complete events (original rows)
    complete_events = log_df.copy()
    complete_events[StandardColumnNames.LIFECYCLE_TRANSITION] = LifecycleTransitionType.COMPLETE

    # Create start events (duplicates with same timestamp)
    start_events = log_df.copy()
    start_events[StandardColumnNames.LIFECYCLE_TRANSITION] = LifecycleTransitionType.START

    # Combine start and complete events
    combined_log = pd.concat([start_events, complete_events], ignore_index=True)
    combined_log = combined_log.sort_values(by=[StandardColumnNames.CASE_ID, StandardColumnNames.TIMESTAMP])
    combined_log = combined_log.reset_index(drop=True)

    # Match start/complete pairs and assign instance IDs
    return convert_to_explicit_interval_log(combined_log)


def _process_derivable_interval_log(
    log_df: pd.DataFrame,
    date_format: str | None,
    *,
    dayfirst: bool,
) -> pd.DataFrame:
    """
    Process a derivable interval event log.

    Derivable logs have lifecycle_transition (start/complete) but no instance IDs.
    The match function is used to pair start and complete events.

    Args:
        log_df: The standardized event log.
        date_format: The datetime format.
        dayfirst: Whether to interpret ambiguous dates as day-first.

    Returns:
        pd.DataFrame: An explicit interval log.

    """
    # Convert timestamp to datetime
    _convert_timestamp_column(log_df, StandardColumnNames.TIMESTAMP, date_format, dayfirst=dayfirst)

    # Match start/complete pairs and assign instance IDs
    return convert_to_explicit_interval_log(log_df)


def _process_production_style_log(
    log_df: pd.DataFrame,
    date_format: str | None,
    *,
    dayfirst: bool,
) -> pd.DataFrame:
    """
    Process a production-style event log with start and end timestamps.

    Production logs have a start_timestamp and timestamp (end) for each row.
    Each row is split into start and complete events.

    Args:
        log_df: The standardized event log.
        date_format: The datetime format.
        dayfirst: Whether to interpret ambiguous dates as day-first.

    Returns:
        pd.DataFrame: An explicit interval log.

    """
    # Convert timestamp columns to datetime
    _convert_timestamp_column(log_df, StandardColumnNames.TIMESTAMP, date_format, dayfirst=dayfirst)
    _convert_timestamp_column(log_df, StandardColumnNames.START_TIMESTAMP, date_format, dayfirst=dayfirst)

    # Create start events (use start_timestamp as timestamp)
    start_events = log_df.copy()
    start_events[StandardColumnNames.TIMESTAMP] = start_events[StandardColumnNames.START_TIMESTAMP]
    start_events = start_events.drop(columns=[StandardColumnNames.START_TIMESTAMP])
    start_events[StandardColumnNames.LIFECYCLE_TRANSITION] = LifecycleTransitionType.START

    # Create complete events (use original timestamp)
    complete_events = log_df.drop(columns=[StandardColumnNames.START_TIMESTAMP])
    complete_events[StandardColumnNames.LIFECYCLE_TRANSITION] = LifecycleTransitionType.COMPLETE

    # Combine start and complete events
    combined_log = pd.concat([start_events, complete_events], ignore_index=True)
    combined_log = combined_log.sort_values(by=[StandardColumnNames.CASE_ID, StandardColumnNames.TIMESTAMP])
    combined_log = combined_log.reset_index(drop=True)

    # Match start/complete pairs and assign instance IDs
    return convert_to_explicit_interval_log(combined_log)


def _fix_orphaned_events(log_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix orphaned events in an explicit interval log.

    - Drop start events with no matching complete event (same instance)
    - Add start events for complete events with no matching start event (same instance)

    Args:
        log_df: The explicit interval log with potential orphaned events.

    Returns:
        pd.DataFrame: The log with orphaned events fixed.

    """
    log_df = log_df.copy()

    # Group by case_id and instance to find orphaned events
    grouped = log_df.groupby([StandardColumnNames.CASE_ID, StandardColumnNames.INSTANCE])

    rows_to_drop = []
    rows_to_add = []

    for (case_id, instance_id), group in grouped:  # noqa: B007
        has_start = (group[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.START.value).any()
        has_complete = (group[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.COMPLETE.value).any()

        if has_start and not has_complete:
            # Drop all start events for this instance (orphaned start)
            start_indices = group[
                group[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.START.value
            ].index
            rows_to_drop.extend(start_indices.tolist())

        elif has_complete and not has_start:
            # Add start event(s) for complete event(s) (orphaned complete)
            complete_events = group[
                group[StandardColumnNames.LIFECYCLE_TRANSITION] == LifecycleTransitionType.COMPLETE.value
            ]

            for _, complete_event in complete_events.iterrows():
                # Create a start event with the same data but different lifecycle transition
                start_event = complete_event.copy()
                start_event[StandardColumnNames.LIFECYCLE_TRANSITION] = LifecycleTransitionType.START.value
                # Use the complete event's timestamp for the start event as well
                # (this maintains the same timestamp since we don't know the actual start time)
                rows_to_add.append(start_event)

    # Drop orphaned start events
    if rows_to_drop:
        log_df = log_df.drop(index=rows_to_drop)

    # Add missing start events
    if rows_to_add:
        new_rows_df = pd.DataFrame(rows_to_add)
        log_df = pd.concat([log_df, new_rows_df], ignore_index=True)

    return log_df


def _process_explicit_interval_log(
    log_df: pd.DataFrame,
    date_format: str | None,
    *,
    dayfirst: bool,
) -> pd.DataFrame:
    """
    Process an explicit interval event log.

    Explicit logs already have lifecycle_transition and instance IDs.
    However, they may have orphaned events (start without complete or complete without start).

    Processing:
        1. Convert timestamp to datetime
        2. Identify and handle orphaned events:
           - Drop start events with no matching complete event
           - Add start events for complete events with no matching start event

    Args:
        log_df: The standardized event log.
        date_format: The datetime format.
        dayfirst: Whether to interpret ambiguous dates as day-first.

    Returns:
        pd.DataFrame: The explicit interval log with orphaned events fixed.

    """
    # Convert timestamp to datetime
    _convert_timestamp_column(log_df, StandardColumnNames.TIMESTAMP, date_format, dayfirst=dayfirst)

    # Fix orphaned events
    log_df = _fix_orphaned_events(log_df)

    # Sort by case_id and timestamp for consistency
    log_df = log_df.sort_values(by=[StandardColumnNames.CASE_ID, StandardColumnNames.TIMESTAMP])

    return log_df.reset_index(drop=True)
