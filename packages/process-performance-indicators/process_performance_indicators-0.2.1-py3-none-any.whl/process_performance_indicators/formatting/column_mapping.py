from dataclasses import asdict, dataclass
from typing import ClassVar

from process_performance_indicators.constants import StandardColumnNames


@dataclass
class StandardColumnMapping:
    """
    Dataclass for mapping log columns to standard column names.
    Each field represents a standard column name, and the value is the corresponding column name in the log.
    """

    # Mandatory columns
    case_id_key: str
    activity_key: str
    timestamp_key: str

    # Optional columns
    start_timestamp_key: str | None = None
    total_cost_key: str | None = None
    human_resource_key: str | None = None
    role_key: str | None = None
    resource_key: str | None = None
    outcome_unit_key: str | None = None
    unsuccessful_outcome_unit_key: str | None = None
    fixed_cost_key: str | None = None
    variable_cost_key: str | None = None
    labor_cost_key: str | None = None
    inventory_cost_key: str | None = None
    client_key: str | None = None
    maintenance_cost_key: str | None = None
    missed_deadline_cost_key: str | None = None
    transportation_cost_key: str | None = None
    warehousing_cost_key: str | None = None
    quality_key: str | None = None
    lifecycle_type_key: str | None = None
    instance_key: str | None = None

    _field_to_standard: ClassVar[dict[str, str]] = {
        "case_id_key": StandardColumnNames.CASE_ID,
        "activity_key": StandardColumnNames.ACTIVITY,
        "timestamp_key": StandardColumnNames.TIMESTAMP,
        "start_timestamp_key": StandardColumnNames.START_TIMESTAMP,
        "total_cost_key": StandardColumnNames.TOTAL_COST,
        "human_resource_key": StandardColumnNames.HUMAN_RESOURCE,
        "role_key": StandardColumnNames.ROLE,
        "resource_key": StandardColumnNames.ORG_RESOURCE,
        "outcome_unit_key": StandardColumnNames.OUTCOME_UNIT,
        "unsuccessful_outcome_unit_key": StandardColumnNames.UNSUCCESSFUL_OUTCOME_UNIT,
        "fixed_cost_key": StandardColumnNames.FIXED_COST,
        "variable_cost_key": StandardColumnNames.VARIABLE_COST,
        "labor_cost_key": StandardColumnNames.LABOR_COST,
        "inventory_cost_key": StandardColumnNames.INVENTORY_COST,
        "client_key": StandardColumnNames.CLIENT,
        "maintenance_cost_key": StandardColumnNames.MAINTENANCE_COST,
        "missed_deadline_cost_key": StandardColumnNames.MISSED_DEADLINE_COST,
        "transportation_cost_key": StandardColumnNames.TRANSPORTATION_COST,
        "warehousing_cost_key": StandardColumnNames.WAREHOUSING_COST,
        "quality_key": StandardColumnNames.QUALITY,
        "lifecycle_type_key": StandardColumnNames.LIFECYCLE_TRANSITION,
        "instance_key": StandardColumnNames.INSTANCE,
    }

    def to_standard_mapping(self) -> dict[str, str]:
        """
        Convert the dataclass to a log-to-standard mapping dictionary.

        Returns:
            Dict[str, str]: A dictionary where keys are standard column names and values are log column names.

        """
        mapping = {}
        for field_name, field_value in asdict(self).items():
            if field_value is not None and field_name in self._field_to_standard:
                standard_name = self._field_to_standard[field_name]
                mapping[standard_name] = field_value
        return mapping


def convert_to_standard_mapping(mapping: StandardColumnMapping) -> dict[str, str]:
    """
    Convert either a dictionary or StandardColumnMapping instance to a standard column mapping dictionary.

    Args:
        mapping: Either a dictionary mapping standard column names to log column names,
                or a StandardColumnMapping instance.

    Returns:
        Dict[str, str]: A dictionary where keys are standard column names and values are log column names.

    """
    return mapping.to_standard_mapping()


def validate_column_mapping(mapping: dict[str, str], existing_columns: set[str]) -> bool:
    """
    Validate the column mapping to ensure all columns exist in the event log.

    Args:
        mapping: The column mapping to validate with standard column names as keys.
        existing_columns: The columns that exist in the event log.

    Returns:
        bool: True if the mapping is valid.

    Raises:
        ValueError: If any column in the mapping is not present in the event log.

    """
    missing_columns = [col for col in mapping.values() if col not in existing_columns]
    if missing_columns:
        raise ValueError(f"Mapping refers to columns that do not exist in the event log: {missing_columns}")
    return True
