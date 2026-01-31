from enum import Enum


class StandardColumnNames(str, Enum):
    """Enum representing standard column names in process mining event logs."""

    CASE_ID = "case:concept:name"
    ACTIVITY = "concept:name"
    TIMESTAMP = "time:timestamp"
    START_TIMESTAMP = "start_timestamp"
    LIFECYCLE_TRANSITION = "lifecycle:transition"
    INSTANCE = "concept:instance"
    HUMAN_RESOURCE = "human_resource"
    ROLE = "org:role"
    ORG_RESOURCE = "org:resource"
    OUTCOME_UNIT = "outcome_unit"
    UNSUCCESSFUL_OUTCOME_UNIT = "unsuccessful_outcome_unit"
    TOTAL_COST = "cost:total"
    FIXED_COST = "cost:fixed"
    VARIABLE_COST = "cost:variable"
    LABOR_COST = "cost:labor"
    INVENTORY_COST = "cost:inventory"
    MAINTENANCE_COST = "cost:maintenance"
    MISSED_DEADLINE_COST = "cost:missed_deadline"
    TRANSPORTATION_COST = "cost:transportation"
    WAREHOUSING_COST = "cost:warehousing"
    CLIENT = "client"
    QUALITY = "quality"


class LifecycleTransitionType(str, Enum):
    """Enum representing the lifecycle transition of an event."""

    START = "start"
    COMPLETE = "complete"
