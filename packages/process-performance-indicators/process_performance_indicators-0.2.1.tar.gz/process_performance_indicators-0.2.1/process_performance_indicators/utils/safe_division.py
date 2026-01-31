"""
Safe division utilities for process performance indicators.

This module provides a simple function for performing division operations
with appropriate error handling.
"""

from typing import overload

import pandas as pd

from process_performance_indicators.exceptions import IndicatorDivisionError

DECIMALS = 3


@overload
def safe_division(
    numerator: float,
    denominator: float,
    exception_class: type[Exception] = IndicatorDivisionError,
) -> float: ...


@overload
def safe_division(
    numerator: pd.Timedelta,
    denominator: float,
    exception_class: type[Exception] = IndicatorDivisionError,
) -> pd.Timedelta: ...


@overload
def safe_division(
    numerator: pd.Timedelta,
    denominator: pd.Timedelta,
    exception_class: type[Exception] = IndicatorDivisionError,
) -> float: ...


def safe_division(
    numerator: float | pd.Timedelta,
    denominator: float | pd.Timedelta,
    exception_class: type[Exception] = IndicatorDivisionError,
) -> float | pd.Timedelta:
    """
    Safely perform division with automatic error handling.

    Args:
        numerator: The numerator value (float or pd.Timedelta).
        denominator: The denominator value (float or pd.Timedelta, integers are automatically converted).
        exception_class: The exception class to raise (defaults to ProcessPerformanceIndicatorDivisionError).

    Returns:
        float: When numerator is float or when both are pd.Timedelta (dimensionless ratio).
        pd.Timedelta: When numerator is pd.Timedelta and denominator is float.

    Raises:
        exception_class: When denominator is zero, with a message showing both values.

    """
    # Check for zero denominator (handle both numeric and Timedelta types)
    if (isinstance(denominator, pd.Timedelta) and denominator == pd.Timedelta(0)) or (
        not isinstance(denominator, pd.Timedelta) and denominator == 0
    ):
        error_message = f"Division error: cannot divide {numerator} by {denominator}."
        raise exception_class(error_message)
    # Type-safe division with explicit type handling
    # The overloads ensure only valid combinations reach here
    if isinstance(numerator, pd.Timedelta) or isinstance(denominator, pd.Timedelta):
        return numerator / denominator  # type: ignore[operator]

    return round(numerator / denominator, DECIMALS)
