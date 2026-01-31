import pandas as pd

from process_performance_indicators.constants import StandardColumnNames
from process_performance_indicators.exceptions import ActivityNameNotFoundError
from process_performance_indicators.utils.column_validation import assert_column_exists


def events(event_log: pd.DataFrame, activity_name: str) -> pd.DataFrame:
    """
    Get the events dataframe of an activity.
    """
    _is_activity_name_valid(event_log, activity_name)

    return event_log[event_log[StandardColumnNames.ACTIVITY] == activity_name]


def res(event_log: pd.DataFrame, activity_name: str) -> set:
    """
    Get the resources names set of an activity.
    """
    _is_activity_name_valid(event_log, activity_name)
    assert_column_exists(event_log, StandardColumnNames.ORG_RESOURCE)

    resources = event_log[event_log[StandardColumnNames.ACTIVITY] == activity_name][
        StandardColumnNames.ORG_RESOURCE
    ].unique()
    return set(resources.tolist())


def hres(event_log: pd.DataFrame, activity_name: str) -> set:
    """
    Get the human resources names set of an activity.
    """
    _is_activity_name_valid(event_log, activity_name)
    assert_column_exists(event_log, StandardColumnNames.HUMAN_RESOURCE)

    human_resources = event_log[event_log[StandardColumnNames.ACTIVITY] == activity_name][
        StandardColumnNames.HUMAN_RESOURCE
    ].unique()

    return set(human_resources.tolist())


def role(event_log: pd.DataFrame, activity_name: str) -> set:
    """
    Get the roles names set of an activity.
    """
    _is_activity_name_valid(event_log, activity_name)
    assert_column_exists(event_log, StandardColumnNames.ROLE)

    roles = event_log[event_log[StandardColumnNames.ACTIVITY] == activity_name][StandardColumnNames.ROLE].unique()

    return set(roles.tolist())


def inst(event_log: pd.DataFrame, activity_name: str) -> set:
    """
    Get the instances ids set of an activity.
    """
    _is_activity_name_valid(event_log, activity_name)
    assert_column_exists(event_log, StandardColumnNames.INSTANCE)

    instances = event_log[event_log[StandardColumnNames.ACTIVITY] == activity_name][
        StandardColumnNames.INSTANCE
    ].unique()

    # Convert to list first to avoid issues with numpy types in set
    return set(instances.tolist())


def _is_activity_name_valid(event_log: pd.DataFrame, activity_name: str) -> None:
    """
    Check if the activity name is valid.
    """
    if activity_name not in event_log[StandardColumnNames.ACTIVITY].unique():
        raise ActivityNameNotFoundError(f"Activity name {activity_name} not found in event log.")
