import pandas as pd

import process_performance_indicators.utils.cases as cases_utils


def variants(event_log: pd.DataFrame, case_ids: list[str] | set[str]) -> set[tuple[str, ...]]:
    """
    Returns a list of variants, based on the sequences of the cases.
    """
    variants = set()
    for case_id in case_ids:
        variants.update(cases_utils.trace(event_log, case_id))
    return variants
