# Process Performance Indicators

A Python library for calculating **310 process performance indicators** from event logs. The library supports multiple event log formats and provides indicators across 5 dimensions (Time, Cost, Quality, Flexibility, General) at 4 granularity levels (activities, cases, groups, instances).

## Features

- **Comprehensive indicator coverage**: 310 indicators across time, cost, quality, flexibility, and general dimensions
- **Multiple granularities**: Calculate metrics at activity, case, group, or instance level
- **Flexible input formats**: Support for atomic, derivable, production-style, and explicit interval event logs
- **Automatic format detection**: The library detects your log format and converts it to the required structure
- **Batch execution**: Run all indicators at once or filter by dimension/granularity

## Quick Installation

=== "uv"

    ```bash
    uv add process-performance-indicators
    ```

=== "pip"

    ```bash
    pip install process-performance-indicators
    ```

## Quick Start

```python
import pandas as pd
from process_performance_indicators import (
    event_log_formatter,
    run_indicators_to_csv,
    StandardColumnMapping,
    IndicatorArguments,
)

# 1. Load your event log
raw_log = pd.read_csv("my_event_log.csv")

# 2. Define column mapping
column_mapping = StandardColumnMapping(
    case_id_key="CaseID",
    activity_key="Activity",
    timestamp_key="Timestamp",
)

# 3. Format the event log
formatted_log = event_log_formatter(raw_log, column_mapping)

# 4. Define indicator arguments
args = IndicatorArguments(
    case_id="CASE-001",
    activity_name="Review Application",
)

# 5. Run indicators and save results
results = run_indicators_to_csv(
    formatted_log,
    args,
    csv_path="results.csv",
    verbose=True,
)

print(results.head())
```

## Next Steps

- [Installation](installation.md) - Detailed installation instructions
- [Usage Guide](usage.md) - Learn how to load, format, and analyze event logs
- [Examples](examples.md) - Working examples with sample datasets
- [API Reference](reference/general.md) - Explore all available indicators
