"""Core indicator execution functions."""

import inspect
from dataclasses import asdict
from typing import Any

import pandas as pd
from tqdm import tqdm

from process_performance_indicators.execution._helpers import (
    missing_required_args,
    normalize_result,
)
from process_performance_indicators.execution._registry import select_indicators
from process_performance_indicators.execution.models import IndicatorArguments


def run_indicators(
    event_log: pd.DataFrame,
    args: IndicatorArguments,
    *,
    dimension: list[str] | None = None,
    granularity: list[str] | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Runs process performance indicators on the provided event log with the given arguments.

    This function selects and executes indicator functions (based on dimension and granularity filters)
    using the arguments provided in `args`. It handles missing arguments, captures errors,
    and collects results in a DataFrame format suitable for CSV export or further analysis.

    Args:
        event_log (pd.DataFrame): The formatted event log on which to run the indicators.
        args (IndicatorArguments): Parameter values to supply to indicators as needed.
        dimension (list[str] | None, optional): Filter to include only specified dimensions (e.g., ["cost", "time"]). Use None to include all.
        granularity (list[str] | None, optional): Filter to include only specified granularities (e.g., ["cases", "groups"]). Use None to include all.
        verbose (bool, optional): If True, logs progress of indicator execution.

    Returns:
        pd.DataFrame: DataFrame with one row per indicator execution, including columns for
        dimension, granularity, indicator name, status (success/error), error message, and result.

    """
    selected = select_indicators(dimension=dimension, granularity=granularity)

    args_dict = {k: v for k, v in asdict(args).items() if v is not None}

    rows: list[dict[str, Any]] = []
    total = len(selected)

    iterator = tqdm(
        selected,
        total=total,
        desc="Running indicators",
        disable=not verbose,
        unit="indicator",
    )

    for spec in iterator:
        if verbose:
            iterator.set_postfix_str(f"Calculating {spec.name}")

        indicator = spec.callable
        sig = inspect.signature(indicator)

        # Build kwargs: always provide event_log; provide args matching parameter names.
        kwargs: dict[str, Any] = {"event_log": event_log}
        for param_name in sig.parameters:
            if param_name == "event_log":
                continue
            if param_name in args_dict:
                kwargs[param_name] = args_dict[param_name]

        missing = missing_required_args(sig, kwargs)

        base_row = {
            "dimension": spec.dimension,
            "granularity": spec.granularity,
            "indicator_name": spec.name,
        }

        if missing:
            rows.append(
                {
                    **base_row,
                    **normalize_result(None),
                    "status": f"Missing required args: {missing}",
                }
            )
            continue

        try:
            result = indicator(**kwargs)
            rows.append(
                {
                    **base_row,
                    **normalize_result(result),
                    "status": "Success",
                }
            )
        except Exception as e:  # noqa: BLE001
            rows.append(
                {
                    **base_row,
                    **normalize_result(None),
                    "status": str(e),
                }
            )

    return pd.DataFrame(rows)


def run_indicators_to_csv(  # noqa: PLR0913
    event_log: pd.DataFrame,
    args: IndicatorArguments,
    *,
    csv_path: str,
    dimension: list[str] | None = None,
    granularity: list[str] | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Runs indicators and saves the results to CSV.

    This function runs indicators on the provided event log with the given arguments,
    and saves the results to a CSV file. It uses the `run_indicators` function to execute
    the indicators and the `pd.DataFrame.to_csv` method to save the results.

    Args:
        event_log (pd.DataFrame): The formatted event log on which to run the indicators.
        args (IndicatorArguments): Parameter values to supply to indicators as needed.
        csv_path (str): The path to the CSV file to save the results to.
        dimension (list[str] | None, optional): Filter to include only specified dimensions (e.g., ["cost", "time"]). Use None to include all.
        granularity (list[str] | None, optional): Filter to include only specified granularities (e.g., ["cases", "groups"]). Use None to include all.
        verbose (bool, optional): If True, logs progress of indicator execution.

    Returns:
        pd.DataFrame: DataFrame with one row per indicator execution, including columns for
        dimension, granularity, indicator name, status (success/error), error message, and result.

    """
    results_df = run_indicators(event_log, args, dimension=dimension, granularity=granularity, verbose=verbose)
    results_df.to_csv(csv_path, index=False)
    return results_df
