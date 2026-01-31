import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from process_performance_indicators.constants import StandardColumnNames

# Cache directory - can be overridden via environment variable
_CACHE_DIR = Path(os.getenv("PPI_CACHE_DIR", Path.home() / ".cache" / "process_performance_indicators"))
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Module-level in-memory caches
_trace_cache: dict[str, dict[str, set[tuple[str, ...]]]] = {}
_sequence_cache: dict[str, dict[str, set[tuple[str, ...]]]] = {}


def _compute_event_log_hash(event_log: pd.DataFrame) -> str:
    """
    Compute a hash of the event log based on relevant columns for trace/sequence computation.
    Uses CASE_ID, ACTIVITY, TIMESTAMP, INSTANCE (if present), and LIFECYCLE_TRANSITION (if present).

    Args:
        event_log: The event log DataFrame.

    Returns:
        SHA256 hash as hex string.

    """
    # Sort by case_id and timestamp for consistent hashing
    relevant_cols = [
        StandardColumnNames.CASE_ID,
        StandardColumnNames.ACTIVITY,
        StandardColumnNames.TIMESTAMP,
    ]

    # Add optional columns if present
    if StandardColumnNames.INSTANCE in event_log.columns:
        relevant_cols.append(StandardColumnNames.INSTANCE)
    if StandardColumnNames.LIFECYCLE_TRANSITION in event_log.columns:
        relevant_cols.append(StandardColumnNames.LIFECYCLE_TRANSITION)

    # Get only relevant columns and sort for consistent hashing
    df_subset = event_log[relevant_cols].sort_values(by=relevant_cols)

    # Convert to string representation and hash
    # Using to_csv with index=False for consistent representation
    df_str = df_subset.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(df_str).hexdigest()


def _get_cache_file_path(event_log_hash: str, cache_type: str) -> Path:
    """
    Get the cache file path for a given event log hash and cache type.

    Args:
        event_log_hash: The hash of the event log.
        cache_type: Either "traces" or "sequences".

    Returns:
        Path to the cache file.

    """
    return _CACHE_DIR / f"{cache_type}_{event_log_hash}.json"


def _load_cache(event_log_hash: str, cache_type: str) -> dict[str, set[tuple[str, ...]]] | None:
    """
    Load cache from disk. Returns None if cache doesn't exist or is invalid.

    Args:
        event_log_hash: The hash of the event log.
        cache_type: Either "traces" or "sequences".

    Returns:
        Dictionary mapping case_id to cached values, or None if cache doesn't exist or is corrupted.

    """
    cache_file = _get_cache_file_path(event_log_hash, cache_type)
    if not cache_file.exists():
        return None

    try:
        with cache_file.open() as f:
            cache_data = json.load(f)
            # Convert lists back to sets of tuples
            return {case_id: {tuple(trace) for trace in traces} for case_id, traces in cache_data.items()}
    except (json.JSONDecodeError, OSError, KeyError, TypeError):
        # If cache is corrupted, return None to trigger recomputation
        return None


def _save_cache(event_log_hash: str, cache: dict[str, set[tuple[str, ...]]], cache_type: str) -> None:
    """
    Save cache to disk. Converts tuples to lists for JSON serialization.

    Args:
        event_log_hash: The hash of the event log.
        cache: Dictionary mapping case_id to cached values.
        cache_type: Either "traces" or "sequences".

    """
    cache_file = _get_cache_file_path(event_log_hash, cache_type)

    # Convert sets of tuples to lists of lists for JSON
    cache_data = {case_id: [list(trace) for trace in traces] for case_id, traces in cache.items()}

    try:
        with cache_file.open("w") as f:
            json.dump(cache_data, f)
    except OSError:
        # Silently fail if we can't write cache (permissions, disk full, etc.)
        pass


def get_trace(event_log: pd.DataFrame, case_id: str) -> set[tuple[str, ...]] | None:
    """
    Get cached trace for a case. Checks in-memory cache first, then disk cache.

    Args:
        event_log: The event log DataFrame.
        case_id: The case ID.

    Returns:
        Cached trace or None if not found.

    """
    event_log_hash = _compute_event_log_hash(event_log)

    # Check in-memory cache first
    if event_log_hash in _trace_cache and case_id in _trace_cache[event_log_hash]:
        return _trace_cache[event_log_hash][case_id]

    # Load from disk cache if not in memory
    if event_log_hash not in _trace_cache:
        disk_cache = _load_cache(event_log_hash, "traces")
        if disk_cache:
            _trace_cache[event_log_hash] = disk_cache
            # Check again after loading from disk
            if case_id in _trace_cache[event_log_hash]:
                return _trace_cache[event_log_hash][case_id]

    return None


def save_trace(event_log: pd.DataFrame, case_id: str, trace: set[tuple[str, ...]]) -> None:
    """
    Save trace to cache (both in-memory and disk).

    Args:
        event_log: The event log DataFrame.
        case_id: The case ID.
        trace: The trace to cache.

    """
    event_log_hash = _compute_event_log_hash(event_log)

    # Initialize cache if needed
    if event_log_hash not in _trace_cache:
        _trace_cache[event_log_hash] = {}

    # Store in memory
    _trace_cache[event_log_hash][case_id] = trace

    # Save to disk
    _save_cache(event_log_hash, _trace_cache[event_log_hash], "traces")


def get_sequence(event_log: pd.DataFrame, case_id: str) -> set[tuple[str, ...]] | None:
    """
    Get cached sequence for a case. Checks in-memory cache first, then disk cache.

    Args:
        event_log: The event log DataFrame.
        case_id: The case ID.

    Returns:
        Cached sequence or None if not found.

    """
    event_log_hash = _compute_event_log_hash(event_log)

    # Check in-memory cache first
    if event_log_hash in _sequence_cache and case_id in _sequence_cache[event_log_hash]:
        return _sequence_cache[event_log_hash][case_id]

    # Load from disk cache if not in memory
    if event_log_hash not in _sequence_cache:
        disk_cache = _load_cache(event_log_hash, "sequences")
        if disk_cache:
            _sequence_cache[event_log_hash] = disk_cache
            # Check again after loading from disk
            if case_id in _sequence_cache[event_log_hash]:
                return _sequence_cache[event_log_hash][case_id]

    return None


def save_sequence(event_log: pd.DataFrame, case_id: str, sequence: set[tuple[str, ...]]) -> None:
    """
    Save sequence to cache (both in-memory and disk).

    Args:
        event_log: The event log DataFrame.
        case_id: The case ID.
        sequence: The sequence to cache.

    """
    event_log_hash = _compute_event_log_hash(event_log)

    # Initialize cache if needed
    if event_log_hash not in _sequence_cache:
        _sequence_cache[event_log_hash] = {}

    # Store in memory
    _sequence_cache[event_log_hash][case_id] = sequence

    # Save to disk
    _save_cache(event_log_hash, _sequence_cache[event_log_hash], "sequences")


def precompute_all_traces(event_log: pd.DataFrame) -> None:
    """
    Precompute all traces for all cases in the event log and cache them.
    This is useful when you know you'll need many traces.

    Args:
        event_log: The event log DataFrame.

    """
    from process_performance_indicators.utils.cases import trace

    event_log_hash = _compute_event_log_hash(event_log)

    # Check if already fully cached
    disk_cache = _load_cache(event_log_hash, "traces")
    all_case_ids = set(event_log[StandardColumnNames.CASE_ID].unique())
    if disk_cache and len(disk_cache) == len(all_case_ids):
        _trace_cache[event_log_hash] = disk_cache
        return

    # Compute all traces (trace() will handle caching automatically)
    cache = {}
    for case_id in all_case_ids:
        cache[case_id] = trace(event_log, case_id)

    # Store in memory and disk
    _trace_cache[event_log_hash] = cache
    _save_cache(event_log_hash, cache, "traces")


def precompute_all_sequences(event_log: pd.DataFrame) -> None:
    """
    Precompute all sequences for all cases in the event log and cache them.
    This is useful when you know you'll need many sequences.

    Args:
        event_log: The event log DataFrame.

    """
    from process_performance_indicators.utils.cases import seq

    event_log_hash = _compute_event_log_hash(event_log)

    # Check if already fully cached
    disk_cache = _load_cache(event_log_hash, "sequences")
    all_case_ids = set(event_log[StandardColumnNames.CASE_ID].unique())
    if disk_cache and len(disk_cache) == len(all_case_ids):
        _sequence_cache[event_log_hash] = disk_cache
        return

    # Compute all sequences
    cache = {}
    for case_id in all_case_ids:
        cache[case_id] = seq(event_log, case_id)

    # Store in memory and disk
    _sequence_cache[event_log_hash] = cache
    _save_cache(event_log_hash, cache, "sequences")


def clear_cache(event_log: pd.DataFrame | None = None, cache_type: str | None = None) -> None:  # noqa: PLR0912
    """
    Clear cache. If event_log is provided, only clear cache for that log.
    If cache_type is provided, only clear that type ("traces" or "sequences").
    If both are None, clear all caches.

    Args:
        event_log: Optional event log DataFrame. If None, clear all event logs.
        cache_type: Optional cache type ("traces" or "sequences"). If None, clear both types.

    """
    if event_log is None:
        # Clear all disk caches
        if cache_type is None:
            for cache_file in _CACHE_DIR.glob("*.json"):
                cache_file.unlink()
            _trace_cache.clear()
            _sequence_cache.clear()
        else:
            for cache_file in _CACHE_DIR.glob(f"{cache_type}_*.json"):
                cache_file.unlink()
            if cache_type == "traces":
                _trace_cache.clear()
            elif cache_type == "sequences":
                _sequence_cache.clear()
    else:
        event_log_hash = _compute_event_log_hash(event_log)
        if cache_type is None:
            # Clear both types for this event log
            for cache_type_name in ["traces", "sequences"]:
                cache_file = _get_cache_file_path(event_log_hash, cache_type_name)
                if cache_file.exists():
                    cache_file.unlink()
            _trace_cache.pop(event_log_hash, None)
            _sequence_cache.pop(event_log_hash, None)
        else:
            # Clear specific type for this event log
            cache_file = _get_cache_file_path(event_log_hash, cache_type)
            if cache_file.exists():
                cache_file.unlink()
            if cache_type == "traces":
                _trace_cache.pop(event_log_hash, None)
            elif cache_type == "sequences":
                _sequence_cache.pop(event_log_hash, None)


def get_cache_info() -> dict[str, Any]:
    """
    Get information about the cache (size, location, etc.).

    Returns:
        Dictionary with cache statistics.

    """
    cache_files = list(_CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in cache_files)

    trace_files = list(_CACHE_DIR.glob("traces_*.json"))
    sequence_files = list(_CACHE_DIR.glob("sequences_*.json"))

    return {
        "cache_directory": str(_CACHE_DIR),
        "total_cache_files": len(cache_files),
        "trace_cache_files": len(trace_files),
        "sequence_cache_files": len(sequence_files),
        "total_cache_size_bytes": total_size,
        "in_memory_cached_logs_traces": len(_trace_cache),
        "in_memory_cached_logs_sequences": len(_sequence_cache),
    }
