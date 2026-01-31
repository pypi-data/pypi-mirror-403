"""Private helper functions for indicator execution."""

import inspect
from typing import Any

import pandas as pd


def normalize_result(value: Any) -> dict[str, Any]:
    """Normalize arbitrary indicator outputs into CSV-friendly columns."""
    if value is None:
        result = ""
    elif isinstance(value, pd.Timestamp):
        result = value.isoformat()
    else:
        result = str(value)

    return {"result": result}


def missing_required_args(sig: inspect.Signature, kwargs: dict[str, Any]) -> list[str]:
    """Identify missing required arguments for a function signature."""
    missing: list[str] = []
    for name, param in sig.parameters.items():
        if name == "event_log":
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if param.default is not inspect.Parameter.empty:
            continue
        if name not in kwargs:
            missing.append(name)
    return missing
