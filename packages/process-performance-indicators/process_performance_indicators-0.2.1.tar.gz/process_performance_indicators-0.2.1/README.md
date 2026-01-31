# Process Performance Indicators

A Python library for calculating **310 process performance indicators** from event logs. The library supports multiple event log formats and provides indicators across 5 dimensions (Time, Cost, Quality, Flexibility, General) at 4 granularity levels (activities, cases, groups, instances).

## Features

- **Comprehensive indicator coverage**: 310 indicators across time, cost, quality, flexibility, and general dimensions
- **Multiple granularities**: Calculate metrics at activity, case, group, or instance level
- **Flexible input formats**: Support for atomic, derivable, production-style, and explicit interval event logs
- **Automatic format detection**: The library detects your log format and converts it to the required structure
- **Batch execution**: Run all indicators at once or filter by dimension/granularity

## Installation

### From PyPI

```bash
# Using uv (recommended)
uv add process-performance-indicators

# Using pip
pip install process-performance-indicators
```

### From Source

```bash
git clone https://github.com/nicoabarca/process-performance-indicators.git
cd process-performance-indicators
uv sync --dev  # or: pip install -e .
```

### Requirements

- Python 3.10 or higher
- pandas >= 2.2.3
- tqdm >= 4.67.1

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

## Event Log Formats

The library supports **4 event log formats**:

| Format                 | Description                                 | Required Columns                                     |
| ---------------------- | ------------------------------------------- | ---------------------------------------------------- |
| **Atomic**             | Simplest format with single timestamp       | case_id, activity, timestamp                         |
| **Derivable Interval** | Has lifecycle transitions (start/complete)  | case_id, activity, timestamp, lifecycle              |
| **Production-Style**   | Separate start and end timestamps           | case_id, activity, start_timestamp, end_timestamp    |
| **Explicit Interval**  | Full format with lifecycle and instance IDs | case_id, activity, timestamp, lifecycle, instance_id |

The `event_log_formatter()` function automatically detects your format and converts it to explicit interval format.

## Indicator Dimensions and Granularities

### Dimensions

| Dimension       | Description                  | Examples                                           |
| --------------- | ---------------------------- | -------------------------------------------------- |
| **Time**        | Duration and timing metrics  | Lead time, service time, waiting time, cycle time  |
| **Cost**        | Financial metrics            | Total cost, labor cost, fixed/variable cost ratios |
| **Quality**     | Output and success metrics   | Outcome units, success rate, rework percentage     |
| **Flexibility** | Adaptability metrics         | Activity flexibility, resource flexibility         |
| **General**     | Count and occurrence metrics | Activity count, case count, rework count           |

### Granularities

| Granularity    | Scope                        | Example                                 |
| -------------- | ---------------------------- | --------------------------------------- |
| **instances**  | Single activity execution    | Service time for instance "inst-001"    |
| **activities** | All instances of an activity | Total lead time for "Review" activity   |
| **cases**      | All activities in a case     | Total cost for case "C1"                |
| **groups**     | Multiple cases (filtered)    | Average cycle time for cases in January |

## Running Indicators

### Single Indicator

```python
from process_performance_indicators.indicators.time import activities as time_activities

lead_time = time_activities.lead_time(formatted_log, activity_name="Review")
```

### Multiple Indicators

```python
from process_performance_indicators import run_indicators, IndicatorArguments

args = IndicatorArguments(
    case_id="C1",
    activity_name="Review",
    aggregation_mode="sgl",
)

# Run all indicators
results = run_indicators(formatted_log, args, verbose=True)

# Or filter by dimension/granularity
results = run_indicators(
    formatted_log,
    args,
    dimension=["time", "cost"],
    granularity=["cases"],
)
```

### Saving Results

```python
from process_performance_indicators import run_indicators_to_csv

results = run_indicators_to_csv(
    formatted_log,
    args,
    csv_path="indicator_results.csv",
    verbose=True,
)
```

## Examples

The [examples/](examples/) folder contains working examples with multiple datasets:

- **Datasets**: 9 sample event logs in various formats (atomic, derivable, production-style, explicit)
- **Execution script**: `execute_indicators.py` demonstrates the full pipeline
- **Configuration**: `dataset_configs.json` provides column mappings for each dataset
- **Batch runner**: `run_all_examples.sh` executes all examples

To run all examples:

```bash
cd examples
./run_all_examples.sh
```

See the [Examples documentation](https://nicoabarca.github.io/process-performance-indicators/examples/) for detailed usage.

## Documentation

Full documentation is available at: **https://nicoabarca.github.io/process-performance-indicators/**

- [Installation](https://nicoabarca.github.io/process-performance-indicators/installation/) - Detailed installation instructions
- [Usage Guide](https://nicoabarca.github.io/process-performance-indicators/usage/) - Learn how to load, format, and analyze event logs
- [Examples](https://nicoabarca.github.io/process-performance-indicators/examples/) - Working examples with sample datasets
- [API Reference](https://nicoabarca.github.io/process-performance-indicators/reference/general/) - Explore all available indicators
