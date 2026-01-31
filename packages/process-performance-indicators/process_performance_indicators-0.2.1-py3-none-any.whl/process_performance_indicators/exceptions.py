class ColumnNotFoundError(Exception):
    """
    Exception raised when a column is not found in the event log.
    """


class ActivityNameNotFoundError(Exception):
    """
    Exception raised when an activity name is not found in the event log.
    """


class InstanceIdNotFoundError(Exception):
    """
    Exception raised when an instance id is not found in the event log.
    """


class CaseIdNotFoundError(Exception):
    """
    Exception raised when a case id is not found in the event log.
    """


class NoStartEventFoundError(Exception):
    """
    Exception raised when no start event is found in the event log.
    """


class NoCompleteEventFoundError(Exception):
    """
    Exception raised when no complete event is found in the event log.
    """


class IndicatorDivisionError(Exception):
    """
    Exception raised when the indicator division cannot be calculated.
    """
