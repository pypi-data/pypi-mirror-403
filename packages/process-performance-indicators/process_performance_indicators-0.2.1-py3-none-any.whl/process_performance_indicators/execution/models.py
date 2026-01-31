"""Data models and type definitions for indicator execution."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import pandas as pd

AllowedDimension = Literal["cost", "time", "quality", "flexibility", "general"]
AllowedGranularity = Literal["activities", "cases", "groups", "instances"]


@dataclass(frozen=True)
class IndicatorSpec:
    """Specification for an indicator function."""

    dimension: AllowedDimension
    granularity: AllowedGranularity
    name: str
    callable: Any
    module: str


@dataclass(frozen=True)
class IndicatorArguments:
    """Arguments for running indicators on an event log."""

    # Core entities
    case_id: str | None = None
    case_ids: set[str] | None = None
    activity_name: str | None = None
    instance_id: str | None = None

    # Cross-activity / time-window params
    activity_a: str | None = None
    activity_b: str | None = None
    start_time: pd.Timestamp | datetime | None = None
    end_time: pd.Timestamp | datetime | None = None

    # Start|end activity is "a" for a group of cases
    a_activity_name: str | None = None

    # Resources / org
    human_resource_name: str | None = None
    role_name: str | None = None

    # Sets of activities
    automated_activities: set[str] | None = None
    desired_activities: set[str] | None = None
    unwanted_activities: set[str] | None = None
    direct_cost_activities: set[str] | None = None
    activities_subset: set[str] | None = None

    # Thresholds / expectations
    deadline: pd.Timestamp | None = None
    deadline_margin: pd.Timedelta | None = None
    expectation: pd.Timedelta | None = None
    lead_time_threshold: pd.Timedelta | None = None
    value: str | int | float | None = None

    # Generic modes
    aggregation_mode: Literal["sgl", "sum"] | None = None
    time_aggregation_mode: Literal["s", "c", "sc", "w"] | None = None
