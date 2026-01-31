"""
Column validation utilities for process performance indicators.

This module provides functions for validating the presence of standard columns
in event logs.
"""

import pandas as pd

from process_performance_indicators.constants import StandardColumnNames


def assert_column_exists(event_log: pd.DataFrame, column_name: StandardColumnNames) -> None:
    """
    Assert that a StandardColumnNames enum value exists as a column in the event log.

    Args:
        event_log: The event log DataFrame to check.
        column_name: The StandardColumnNames enum value to look for.

    Raises:
        ValueError: If the column is not present in the event log.

    """
    if column_name.value not in event_log.columns:
        raise ValueError(f"Column '{column_name.value}' is not present in event log.")
