from typing import Literal

import pandas as pd

import process_performance_indicators.indicators.cost.cases as cost_cases_indicators
import process_performance_indicators.indicators.general.groups as general_groups_indicators
import process_performance_indicators.indicators.quality.groups as quality_groups_indicators
import process_performance_indicators.indicators.time.groups as time_groups_indicators
import process_performance_indicators.utils.cases as cases_utils
from process_performance_indicators.exceptions import IndicatorDivisionError
from process_performance_indicators.utils.safe_division import safe_division


def automated_activity_cost(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    automated_activities: set[str],
    aggregation_mode: Literal["sgl", "sum"],
) -> int | float:
    """
    The total cost associated with all instantiations of automated activities in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        automated_activities: The set of automated activities.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    total_cost = 0
    for case_id in case_ids:
        total_cost += cost_cases_indicators.automated_activity_cost(
            event_log, case_id, automated_activities, aggregation_mode
        )
    return total_cost


def expected_automated_activity_cost(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    automated_activities: set[str],
    aggregation_mode: Literal["sgl", "sum"],
) -> int | float:
    """
    The expected total cost associated with all instantiations of automated activities
    in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        automated_activities: The set of automated activities.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    group_automated_activity_cost = automated_activity_cost(event_log, case_ids, automated_activities, aggregation_mode)
    case_group_count = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(group_automated_activity_cost, case_group_count)


def desired_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], desired_activities: set[str]
) -> int:
    """
    The number of instantiated activities whose occurrence is desirable in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        desired_activities: The set of desired activities.

    """
    desired_activity_count = 0
    for case_id in case_ids:
        desired_activity_count += cost_cases_indicators.desired_activity_count(event_log, case_id, desired_activities)
    return desired_activity_count


def expected_desired_activity_count(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], desired_activities: set[str]
) -> float:
    """
    The expected number of instantiated activities whose occurrence is desirable in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        desired_activities: The set of desired activities.

    """
    numerator = desired_activity_count(event_log, case_ids, desired_activities)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def direct_cost(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    direct_cost_activities: set[str],
    aggregation_mode: Literal["sgl", "sum"],
) -> int | float:
    """
    The total cost associated with all instantiations of activities that have a
    direct effect on the outcome of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        direct_cost_activities: The set of activities that have a direct effect on the outcome of the group of cases.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    total_cost = 0
    for case_id in case_ids:
        total_cost += cost_cases_indicators.direct_cost(event_log, case_id, direct_cost_activities, aggregation_mode)
    return total_cost


def expected_direct_cost(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    direct_cost_activities: set[str],
    aggregation_mode: Literal["sgl", "sum"],
) -> int | float:
    """
    The expected total cost associated with all instantiations of activities that have a
    direct effect on the outcome of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        direct_cost_activities: The set of activities that have a direct effect on the outcome of the group of cases.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = direct_cost(event_log, case_ids, direct_cost_activities, aggregation_mode)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def fixed_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The fixed cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    total_fixed_cost = 0

    for case_id in case_ids:
        total_fixed_cost += cost_cases_indicators.fixed_cost(event_log, case_id, aggregation_mode)

    return total_fixed_cost


def expected_fixed_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> int | float | None:
    """
    The expected fixed cost associated with all activity instances of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = fixed_cost(event_log, case_ids, aggregation_mode)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def human_resource_and_case_count_ratio(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float | None:
    """
    The ratio between the number of human resources that are involved in the execution
    of cases in the group of cases, and the number of cases belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    numerator = human_resource_count(event_log, case_ids)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def human_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of human resources that are involved in the execution of cases in
    the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    count = 0
    for case_id in case_ids:
        count += len(cases_utils.hres(event_log, case_id))
    return count


def expected_human_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of human resources that are involved in the execution of cases
    belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    count = 0
    for case_id in case_ids:
        count += cost_cases_indicators.human_resource_count(event_log, case_id)

    numerator = count
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def inventory_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The inventory cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    total_inventory_cost = 0

    for case_id in case_ids:
        total_inventory_cost += cost_cases_indicators.inventory_cost(event_log, case_id, aggregation_mode)

    return total_inventory_cost


def expected_inventory_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The expected inventory cost associated with all activity instances of a case
    belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    numerator = inventory_cost(event_log, case_ids, aggregation_mode)
    denominator = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(numerator, denominator)


def labor_cost_and_total_cost_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the labor cost associated with all activity instances of the group of cases,
    and the total cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        labor_cost(event_log, case_ids, aggregation_mode),
        total_cost(event_log, case_ids, aggregation_mode),
    )


def expected_labor_cost_and_total_cost_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The expected ratio between the labor cost associated with all activity instances of the group of cases,
    and the total cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        labor_cost(event_log, case_ids, aggregation_mode),
        total_cost(event_log, case_ids, aggregation_mode),
    )


def labor_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The labor cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    total_labor_cost = 0

    for case_id in case_ids:
        total_labor_cost += cost_cases_indicators.labor_cost(event_log, case_id, aggregation_mode)

    return total_labor_cost


def expected_labor_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> int | float | None:
    """
    The expected labor cost associated with all activity instances of a case
    belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        labor_cost(event_log, case_ids, aggregation_mode),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def maintenance_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The maintenance cost associated with all cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    total_maintenance_cost: float = 0

    for case_id in case_ids:
        total_maintenance_cost += cost_cases_indicators.maintenance_cost(event_log, case_id)

    return total_maintenance_cost


def expected_maintenance_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected maintenance cost associated with a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(
        maintenance_cost(event_log, case_ids), general_groups_indicators.case_count(event_log, case_ids)
    )


def missed_deadline_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The cost for missing deadlines associated with all cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    total_missed_deadline_cost = 0

    for case_id in case_ids:
        total_missed_deadline_cost += cost_cases_indicators.missed_deadline_cost(event_log, case_id)

    return total_missed_deadline_cost


def expected_missed_deadline_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected cost for missing deadlines associated with a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(
        missed_deadline_cost(event_log, case_ids),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def overhead_cost(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    direct_cost_activities: set[str],
    aggregation_mode: Literal["sgl", "sum"],
) -> float:
    """
    The total cost associated with all instantiations of activities that do not
    have a direct effect on the outcome of the cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        direct_cost_activities: The set of activities that have a direct cost
            on the outcome of the cases.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    total_overhead_cost = 0
    for case_id in case_ids:
        total_overhead_cost += cost_cases_indicators.overhead_cost(
            event_log, case_id, direct_cost_activities, aggregation_mode
        )
    return total_overhead_cost


def expected_overhead_cost(
    event_log: pd.DataFrame,
    case_ids: list[str] | set[str],
    direct_cost_activities: set[str],
    aggregation_mode: Literal["sgl", "sum"],
) -> float:
    """
    The total cost associated with all instantiations of activities that do not have a
    direct effect on the outcome of case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        direct_cost_activities: The set of activities that have a direct cost
            on the outcome of the cases.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        overhead_cost(event_log, case_ids, direct_cost_activities, aggregation_mode),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of resources that are involved in the execution of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    resources = set()
    for case_id in case_ids:
        resources.update(cases_utils.res(event_log, case_id))
    return len(resources)


def expected_resource_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of resources that are involved in the execution of a case belonging
    to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    resource_count = 0
    for case_id in case_ids:
        resource_count += cost_cases_indicators.resource_count(event_log, case_id)
    return safe_division(resource_count, general_groups_indicators.case_count(event_log, case_ids))


def rework_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The total cost of all times that any activity has been instantiated again, after its first
    instantiation, in every case of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    _rework_cost = 0
    for case_id in case_ids:
        _rework_cost += cost_cases_indicators.rework_cost(event_log, case_id, aggregation_mode)
    return _rework_cost


def expected_rework_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The expected total cost of all times that any activity has been instantiated again, after
    its first instantiation, in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        rework_cost(event_log, case_ids, aggregation_mode),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def rework_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> int:
    """
    The number of times that any activity has been instantiated again, after its first intantiation,
    in every case of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    rework_count = 0
    for case_id in case_ids:
        rework_count += cost_cases_indicators.rework_count(event_log, case_id)
    return rework_count


def expected_rework_count(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected number of times that any activity has been instantiated again,
    after its first instantiation, in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(
        rework_count(event_log, case_ids),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def rework_percentage(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The percentage of times that any activity has been instantiated again, after its first
    instantiation, in every case of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(
        rework_count(event_log, case_ids),
        general_groups_indicators.activity_instance_count(event_log, case_ids),
    )


def expected_rework_percentage(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected percentage of times that any activity has been instantiated again, after its first
    instantiation, in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    rework_count = 0
    for case_id in case_ids:
        rework_count += cost_cases_indicators.rework_percentage(event_log, case_id)

    return safe_division(rework_count, general_groups_indicators.case_count(event_log, case_ids))


def total_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The total cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    total_cost = 0

    for case_id in case_ids:
        total_cost += cost_cases_indicators.total_cost(event_log, case_id, aggregation_mode) or 0

    return total_cost


def expected_total_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> int | float | None:
    """
    The expected total cost associated with all activity instances of a case belonging to the
    group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    group_total_cost = total_cost(event_log, case_ids, aggregation_mode)
    case_group_count = general_groups_indicators.case_count(event_log, case_ids)
    return safe_division(group_total_cost, case_group_count)


def total_cost_and_lead_time_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all activity instances of the group of
    cases, and the total elapsed time between the earliest and latest events in the group of cases. In cost per hour.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        total_cost(event_log, case_ids, aggregation_mode),
        time_groups_indicators.lead_time(event_log, case_ids) / pd.Timedelta(hours=1),
    )


def expected_total_cost_and_lead_time_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the expected total cost associated with all activity instances of a case
    belonging to the group of cases, and the expected total elapsed time between the
    earliest and latest timestamps in a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    sum_of_ratios = 0.0
    successful_cases = 0
    last_error: IndicatorDivisionError | None = None

    for case_id in case_ids:
        try:
            sum_of_ratios += cost_cases_indicators.total_cost_and_lead_time_ratio(event_log, case_id, aggregation_mode)
            successful_cases += 1
        except IndicatorDivisionError as e:  # noqa: PERF203
            last_error = e
            continue

    if len(case_ids) > 0 and successful_cases == 0 and last_error is not None:
        raise last_error

    return safe_division(sum_of_ratios, successful_cases) if successful_cases > 0 else 0.0


def total_cost_and_outcome_unit_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all activity instances of the group of
    cases, and the outcome units associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost and outcome unit calculations.
            "sum": Considers the sum of all events of activity instances for cost and outcome unit calculations.

    """
    return safe_division(
        total_cost(event_log, case_ids, aggregation_mode),
        quality_groups_indicators.outcome_unit_count(event_log, case_ids, aggregation_mode),
    )


def expected_total_cost_and_outcome_unit_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the expected total cost associated with all activity instances of a case
    belonging to the group of cases, and the expected outcome units associated with all activity
    instances of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost and outcome unit calculations.
            "sum": Considers the sum of all events of activity instances for cost and outcome unit calculations.

    """
    return safe_division(
        total_cost(event_log, case_ids, aggregation_mode),
        quality_groups_indicators.outcome_unit_count(event_log, case_ids, aggregation_mode),
    )


def total_cost_and_service_time_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the total cost associated with all activity instances of the group of
    cases, and the sum of elapsed times between the start and complete events of all activity
    instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        total_cost(event_log, case_ids, aggregation_mode),
        time_groups_indicators.service_time(event_log, case_ids) / pd.Timedelta(hours=1),
    )


def expected_total_cost_and_service_time_ratio(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The ratio between the expected total cost associated with all activity instances of a case
    belonging to the group of cases, and the expected sum of elapsed times between the start and
    complete events of all activity instances of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    sum_of_ratios = 0.0
    successful_cases = 0
    last_error: IndicatorDivisionError | None = None

    for case_id in case_ids:
        try:
            sum_of_ratios += cost_cases_indicators.total_cost_and_service_time_ratio(
                event_log, case_id, aggregation_mode
            )
            successful_cases += 1
        except IndicatorDivisionError as e:  # noqa: PERF203
            last_error = e
            continue

    if len(case_ids) > 0 and successful_cases == 0 and last_error is not None:
        raise last_error

    return safe_division(sum_of_ratios, successful_cases) if successful_cases > 0 else 0.0


def transportation_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The transportation cost associated with all cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    transportation_cost = 0
    for case_id in case_ids:
        transportation_cost += cost_cases_indicators.transportation_cost(event_log, case_id)
    return transportation_cost


def expected_transportation_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected transportation cost associated with a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(
        transportation_cost(event_log, case_ids),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def variable_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The variable cost associated with all activity instances of the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    variable_cost = 0
    for case_id in case_ids:
        variable_cost += cost_cases_indicators.variable_cost(event_log, case_id, aggregation_mode)
    return variable_cost


def expected_variable_cost(
    event_log: pd.DataFrame, case_ids: list[str] | set[str], aggregation_mode: Literal["sgl", "sum"]
) -> float:
    """
    The expected variable cost associated with all activity instances of a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.
        aggregation_mode: The aggregation mode.
            "sgl": Considers single events of activity instances for cost calculations.
            "sum": Considers the sum of all events of activity instances for cost calculations.

    """
    return safe_division(
        variable_cost(event_log, case_ids, aggregation_mode),
        general_groups_indicators.case_count(event_log, case_ids),
    )


def warehousing_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The warehousing cost associated with all cases in the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    warehousing_cost = 0
    for case_id in case_ids:
        warehousing_cost += cost_cases_indicators.warehousing_cost(event_log, case_id)
    return warehousing_cost


def expected_warehousing_cost(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> float:
    """
    The expected warehousing cost associated with a case belonging to the group of cases.

    Args:
        event_log: The event log.
        case_ids: The case ids.

    """
    return safe_division(
        warehousing_cost(event_log, case_ids),
        general_groups_indicators.case_count(event_log, case_ids),
    )
