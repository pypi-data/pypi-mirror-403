"""Private indicator registry management."""

import inspect
from importlib import import_module

from process_performance_indicators.execution.models import (
    AllowedDimension,
    AllowedGranularity,
    IndicatorSpec,
)

_DIMENSIONS: tuple[AllowedDimension, ...] = ("cost", "time", "quality", "flexibility", "general")
_GRANULARITIES: tuple[AllowedGranularity, ...] = ("activities", "cases", "groups", "instances")


def _iter_indicator_specs_for_module(
    *, dimension: AllowedDimension, granularity: AllowedGranularity, module_name: str
) -> list[IndicatorSpec]:
    """Iterate over indicator specs for a given module."""
    module = import_module(module_name)
    specs: list[IndicatorSpec] = []

    for func_name, func in inspect.getmembers(module, inspect.isfunction):
        if func_name.startswith("_"):
            continue
        # Only functions actually defined in this module (ignore imported helpers).
        if getattr(func, "__module__", None) != module.__name__:
            continue
        specs.append(
            IndicatorSpec(
                dimension=dimension,
                granularity=granularity,
                name=func_name,
                callable=func,
                module=module.__name__,
            )
        )

    specs.sort(key=lambda s: s.name)
    return specs


def _build_indicator_registry() -> list[IndicatorSpec]:
    """Build the explicit indicator registry by enumerating indicator modules."""
    registry: list[IndicatorSpec] = []

    for dimension in _DIMENSIONS:
        for granularity in _GRANULARITIES:
            # flexibility/general don't have instances
            if dimension in {"flexibility", "general"} and granularity == "instances":
                continue
            module_name = f"process_performance_indicators.indicators.{dimension}.{granularity}"
            registry.extend(
                _iter_indicator_specs_for_module(
                    dimension=dimension,
                    granularity=granularity,
                    module_name=module_name,
                )
            )

    registry.sort(key=lambda s: (s.dimension, s.granularity, s.name))
    return registry


_INDICATOR_REGISTRY: list[IndicatorSpec] = _build_indicator_registry()


def select_indicators(
    *,
    dimension: list[str] | None = None,
    granularity: list[str] | None = None,
) -> list[IndicatorSpec]:
    """Filter the registry by dimension and/or granularity (strings-only include filters)."""
    if dimension is not None:
        unknown = sorted(set(dimension).difference(_DIMENSIONS))
        if unknown:
            raise ValueError(f"Unknown dimension(s): {unknown}. Allowed: {list(_DIMENSIONS)}")
    if granularity is not None:
        unknown = sorted(set(granularity).difference(_GRANULARITIES))
        if unknown:
            raise ValueError(f"Unknown granularity(s): {unknown}. Allowed: {list(_GRANULARITIES)}")

    selected: list[IndicatorSpec] = []
    for spec in _INDICATOR_REGISTRY:
        if dimension is not None and spec.dimension not in set(dimension):
            continue
        if granularity is not None and spec.granularity not in set(granularity):
            continue
        selected.append(spec)
    return selected
