# Usage Guide

This guide covers how to load event logs, convert them to the required format, understand the indicator structure, and run performance indicators.

## Loading Event Logs

### CSV Files

The most common format is CSV. Load it using pandas:

```python
import pandas as pd

# Basic CSV loading
event_log = pd.read_csv("my_event_log.csv")

# With specific separator
event_log = pd.read_csv("my_event_log.csv", sep=";")

# With encoding
event_log = pd.read_csv("my_event_log.csv", encoding="utf-8")
```

### XES Files

For XES (eXtensible Event Stream) files, you can use the `pm4py` library to convert to a DataFrame:

```python
import pm4py

# Load XES file
xes_log = pm4py.read_xes("my_event_log.xes")

# Convert to DataFrame
event_log = pm4py.convert_to_dataframe(xes_log)
```

!!! note
    `pm4py` is an optional dependency. Install it with `uv add pm4py` or `pip install pm4py`.

---

## Event Log Formats and Conversion

The library supports **4 event log formats**. The `event_log_formatter()` function automatically detects your format and converts it to the required **explicit interval** format.

### Understanding Log Formats

#### 1. Atomic Logs

The simplest format with only case ID, activity, and a single timestamp per event.

| CaseID | Activity | Timestamp |
|--------|----------|-----------|
| C1 | Submit | 2024-01-01 09:00 |
| C1 | Review | 2024-01-01 10:00 |
| C1 | Approve | 2024-01-01 11:00 |

**Characteristics:**

- No lifecycle information (start/complete)
- No instance IDs
- Each row represents a single event

**Column mapping:**

```python
from process_performance_indicators import StandardColumnMapping

mapping = StandardColumnMapping(
    case_id_key="CaseID",
    activity_key="Activity",
    timestamp_key="Timestamp",
)
```

#### 2. Derivable Interval Logs

Contains lifecycle transitions (start/complete) but no instance IDs. Instance IDs are derived by matching start and complete events.

| CaseID | Activity | Timestamp | Lifecycle |
|--------|----------|-----------|-----------|
| C1 | Submit | 2024-01-01 09:00 | start |
| C1 | Submit | 2024-01-01 09:30 | complete |
| C1 | Review | 2024-01-01 10:00 | start |
| C1 | Review | 2024-01-01 11:00 | complete |

**Characteristics:**

- Has `lifecycle:transition` column with "start" and "complete" values
- No instance IDs (derived from matching)
- Start and complete events must be matched

**Column mapping:**

```python
mapping = StandardColumnMapping(
    case_id_key="CaseID",
    activity_key="Activity",
    timestamp_key="Timestamp",
    lifecycle_type_key="Lifecycle",  # Enables derivable detection
)
```

#### 3. Production-Style Logs

Contains separate columns for start and end timestamps. Common in production/manufacturing systems.

| CaseID | Activity | StartTime | EndTime |
|--------|----------|-----------|---------|
| C1 | Submit | 2024-01-01 09:00 | 2024-01-01 09:30 |
| C1 | Review | 2024-01-01 10:00 | 2024-01-01 11:00 |

**Characteristics:**

- Has both `start_timestamp` and `timestamp` (end) columns
- Each row represents a complete activity execution
- No lifecycle column

**Column mapping:**

```python
mapping = StandardColumnMapping(
    case_id_key="CaseID",
    activity_key="Activity",
    timestamp_key="EndTime",
    start_timestamp_key="StartTime",  # Enables production-style detection
)
```

#### 4. Explicit Interval Logs

The most complete format with lifecycle transitions AND instance IDs.

| CaseID | Activity | Timestamp | Lifecycle | InstanceID |
|--------|----------|-----------|-----------|------------|
| C1 | Submit | 2024-01-01 09:00 | start | inst-001 |
| C1 | Submit | 2024-01-01 09:30 | complete | inst-001 |
| C1 | Review | 2024-01-01 10:00 | start | inst-002 |
| C1 | Review | 2024-01-01 11:00 | complete | inst-002 |

**Characteristics:**

- Has both `lifecycle:transition` and `concept:instance` columns
- Most explicit and complete format
- No matching required

**Column mapping:**

```python
mapping = StandardColumnMapping(
    case_id_key="CaseID",
    activity_key="Activity",
    timestamp_key="Timestamp",
    lifecycle_type_key="Lifecycle",
    instance_key="InstanceID",  # Enables explicit detection
)
```

### Converting Event Logs

Use `event_log_formatter()` to convert any format to the explicit interval format:

```python
from process_performance_indicators import event_log_formatter, StandardColumnMapping
import pandas as pd

# Load raw data
raw_log = pd.read_csv("event_log.csv")

# Define column mapping based on your log format
mapping = StandardColumnMapping(
    case_id_key="CaseID",
    activity_key="Activity",
    timestamp_key="Timestamp",
    # Add optional columns based on your log type
    lifecycle_type_key="Lifecycle",  # For derivable/explicit
    instance_key="InstanceID",        # For explicit only
    # Cost columns
    total_cost_key="Cost",
    # Resource columns
    human_resource_key="Resource",
)

# Format the log (automatic type detection and conversion)
formatted_log = event_log_formatter(
    raw_log,
    column_mapping=mapping,
    date_format=None,   # Auto-detect, or use "ISO8601", "%Y-%m-%d %H:%M:%S", etc.
    dayfirst=False,     # Set True for DD/MM/YYYY formats
)
```

The formatter:

1. Detects your log type based on which columns are mapped
2. Converts timestamps to datetime objects
3. Matches start/complete events (if needed)
4. Assigns instance IDs (if needed)
5. Returns a normalized explicit interval DataFrame

---

## Indicator Structure

### Dimensions

Indicators are organized into **5 dimensions**:

| Dimension | Description | Examples |
|-----------|-------------|----------|
| **Time** | Duration and timing metrics | Lead time, service time, waiting time, cycle time |
| **Cost** | Financial metrics | Total cost, labor cost, fixed/variable cost ratios |
| **Quality** | Output and success metrics | Outcome units, success rate, rework percentage |
| **Flexibility** | Adaptability metrics | Activity flexibility, resource flexibility |
| **General** | Count and occurrence metrics | Activity count, case count, rework count |

### Granularities

Each dimension has indicators at **4 granularity levels**:

| Granularity | Scope | Example |
|-------------|-------|---------|
| **instances** | Single activity execution | Service time for instance "inst-001" |
| **activities** | All instances of an activity | Total lead time for "Review" activity |
| **cases** | All activities in a case | Total cost for case "C1" |
| **groups** | Multiple cases (filtered) | Average cycle time for cases in January |

### Code Organization

Indicators are organized in the codebase as:

```
indicators/
├── time/
│   ├── instances.py    # e.g., lead_time(event_log, instance_id)
│   ├── activities.py   # e.g., lead_time(event_log, activity_name)
│   ├── cases.py        # e.g., lead_time(event_log, case_id)
│   └── groups.py       # e.g., lead_time(event_log, case_ids)
├── cost/
│   ├── instances.py
│   ├── activities.py
│   ├── cases.py
│   └── groups.py
├── quality/
│   └── ...
├── flexibility/
│   └── ...
└── general/
    └── ...
```

---

## Indicator Examples

### Example 1: Time Indicator (Activity Granularity)

Calculate the total lead time for all instances of an activity:

```python
from process_performance_indicators.indicators.time import activities as time_activities

# Calculate lead time for "Review" activity
lead_time = time_activities.lead_time(formatted_log, activity_name="Review")
print(f"Total lead time for Review: {lead_time}")
# Output: Total lead time for Review: 2 days 05:30:00
```

**What it calculates:** Sum of elapsed times (first event to last event) for all instances of the specified activity.

### Example 2: Cost Indicator (Case Granularity)

Calculate the total cost for a specific case:

```python
from process_performance_indicators.indicators.cost import cases as cost_cases

# Calculate total cost for case "C1"
total_cost = cost_cases.total_cost(
    formatted_log,
    case_id="C1",
    aggregation_mode="sgl",  # Use single event per instance
)
print(f"Total cost for case C1: ${total_cost:.2f}")
# Output: Total cost for case C1: $1250.00
```

**Aggregation modes:**

- `"sgl"`: Uses a single event per activity instance for cost calculation
- `"sum"`: Sums costs from all events of each activity instance

### Example 3: Quality Indicator (Case Granularity)

Count automated activities in a case:

```python
from process_performance_indicators.indicators.quality import cases as quality_cases

# Define which activities are automated
automated = {"AutoValidate", "SendNotification", "GenerateReport"}

# Count automated activities in case "C1"
count = quality_cases.automated_activity_count(
    formatted_log,
    case_id="C1",
    automated_activities=automated,
)
print(f"Automated activities in case C1: {count}")
# Output: Automated activities in case C1: 2
```

---

## Running Multiple Indicators

### Using `run_indicators()`

The `run_indicators()` function executes multiple indicators at once:

```python
from process_performance_indicators import run_indicators, IndicatorArguments

# Define arguments for indicators
args = IndicatorArguments(
    case_id="C1",
    activity_name="Review",
    aggregation_mode="sgl",
    automated_activities={"AutoValidate", "SendNotification"},
)

# Run all indicators
results = run_indicators(
    formatted_log,
    args,
    verbose=True,  # Show progress bar
)

print(results.head(10))
```

**Output DataFrame columns:**

| Column | Description |
|--------|-------------|
| `dimension` | time, cost, quality, flexibility, or general |
| `granularity` | activities, cases, groups, or instances |
| `indicator_name` | Name of the indicator function |
| `status` | "Success" or error description |
| `result` | Calculated value (or None if failed) |
| `error_message` | Details if calculation failed |

### Filtering by Dimension/Granularity

Run only specific dimensions or granularities:

```python
# Run only time and cost indicators at case level
results = run_indicators(
    formatted_log,
    args,
    dimension=["time", "cost"],
    granularity=["cases"],
    verbose=True,
)
```

### Saving Results to CSV

Use `run_indicators_to_csv()` for convenience:

```python
from process_performance_indicators import run_indicators_to_csv

results = run_indicators_to_csv(
    formatted_log,
    args,
    csv_path="indicator_results.csv",
    dimension=["time", "cost", "quality"],
    granularity=["cases", "instances"],
    verbose=True,
)
```

### Generating a Summary Report

After running indicators, use `summary_to_csv()` to generate a summary showing how many indicators were successfully calculated by dimension and granularity:

```python
from process_performance_indicators.execution.summary import summary_to_csv

# Generate summary from results
summary = summary_to_csv(
    results_csv_path="indicator_results.csv",
    output_csv_path="indicator_summary.csv",
    formatted_event_log_path="formatted_log.csv",
)

print(summary)
```

**Example output:**

| event_log | relevant_attributes | general_dimension | time_dimension | cost_dimension | quality_dimension | flexibility_dimension | case_granularity | activity_granularity | activity_instance_granularity | group_of_cases_granularity | overall |
|-----------|---------------------|-------------------|----------------|----------------|-------------------|----------------------|------------------|---------------------|------------------------------|---------------------------|---------|
| hospital_log | 8 / 21 | 12 / 15 (80.0%) | 18 / 20 (90.0%) | 10 / 25 (40.0%) | 8 / 12 (66.7%) | 5 / 8 (62.5%) | 20 / 30 (66.7%) | 15 / 25 (60.0%) | 10 / 15 (66.7%) | 8 / 10 (80.0%) | 53 / 80 (66.3%) |

The summary includes:

- **relevant_attributes**: How many of the 21 standard columns exist in your event log
- **dimension columns**: Success rate for each dimension (general, time, cost, quality, flexibility)
- **granularity columns**: Success rate for each granularity level
- **overall**: Total success rate across all indicators

### Complete Example

```python
import pandas as pd
from process_performance_indicators import (
    event_log_formatter,
    run_indicators_to_csv,
    StandardColumnMapping,
    IndicatorArguments,
)

# 1. Load and format event log
raw_log = pd.read_csv("hospital_log.csv")

mapping = StandardColumnMapping(
    case_id_key="PatientID",
    activity_key="Activity",
    timestamp_key="Timestamp",
    lifecycle_type_key="Status",
    total_cost_key="Cost",
    human_resource_key="Doctor",
)

formatted_log = event_log_formatter(raw_log, mapping)

# 2. Get unique cases and activities for analysis
case_ids = formatted_log["case:concept:name"].unique()
activities = formatted_log["concept:name"].unique()

print(f"Found {len(case_ids)} cases and {len(activities)} unique activities")

# 3. Run indicators for a specific case
args = IndicatorArguments(
    case_id=case_ids[0],
    activity_name=activities[0],
    aggregation_mode="sgl",
)

# 4. Execute and save results
results = run_indicators_to_csv(
    formatted_log,
    args,
    csv_path="hospital_indicators.csv",
    verbose=True,
)

# 5. Analyze results
successful = results[results["status"] == "Success"]
print(f"\nSuccessfully calculated {len(successful)} indicators")
print(successful[["dimension", "granularity", "indicator_name", "result"]].head(20))
```

---

## IndicatorArguments Reference

The `IndicatorArguments` dataclass defines all possible parameters for indicators:

```python
from process_performance_indicators import IndicatorArguments

args = IndicatorArguments(
    # Core entities
    case_id="C1",                    # For case-level indicators
    activity_name="Review",          # For activity-level indicators
    instance_id="inst-001",          # For instance-level indicators
    case_ids={"C1", "C2", "C3"},     # For group-level indicators

    # Time windows
    start_time=pd.Timestamp("2024-01-01"),
    end_time=pd.Timestamp("2024-01-31"),

    # Activity sets
    automated_activities={"Auto1", "Auto2"},
    desired_activities={"Good1", "Good2"},
    unwanted_activities={"Bad1"},

    # Thresholds
    deadline=pd.Timestamp("2024-01-15"),
    expectation=pd.Timedelta(days=5),

    # Modes
    aggregation_mode="sgl",  # "sgl" or "sum"
)
```

!!! tip
    Only non-None values are passed to indicator functions. Each indicator declares only the parameters it needs, and the runner automatically provides matching arguments.
