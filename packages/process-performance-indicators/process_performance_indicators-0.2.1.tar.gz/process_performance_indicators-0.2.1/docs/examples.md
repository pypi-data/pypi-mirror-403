# Examples

The [`examples/`](https://github.com/nicoabarca/process-performance-indicators/tree/main/examples) folder contains working examples demonstrating how to use the library with various event log formats and datasets.

## Quick Start

Run all examples at once:

```bash
cd examples
./run_all_examples.sh
```

Or run a single dataset:

```bash
uv run examples/execute_indicators.py \
    --dataset examples/datasets/production.csv \
    --config examples/dataset_configs.json
```

---

## Available Datasets

The `examples/datasets/` folder contains 9 sample event logs covering different formats:

### Synthetic Datasets

| Dataset                                             | Format     | Description                                       |
| --------------------------------------------------- | ---------- | ------------------------------------------------- |
| `atomic_event_log.csv`                              | Atomic     | Simplest format with case/activity/timestamp only |
| `derivable_interval_event_log.csv`                  | Derivable  | With lifecycle transitions (start/complete)       |
| `explicit_interval_event_log.csv`                   | Explicit   | Full format with lifecycle and instance IDs       |
| `timestamp_unique_derivable_interval_event_log.csv` | Derivable  | Derivable format with unique timestamps           |
| `production.csv`                                    | Production | Separate start/end timestamp columns              |

### Real-World Datasets (100-row samples)

| Dataset                                | Description                 |
| -------------------------------------- | --------------------------- |
| `bpi-challenge-2013-incidents_100.csv` | Incident management process |
| `bpi-challenge-2017_100.csv`           | Loan application process    |
| `it-incident_100.csv`                  | IT incident management      |
| `italian-help-desk_100.csv`            | Help desk support process   |

---

## Execution Script

The `execute_indicators.py` script provides a unified entry point for running indicators on any dataset.

### Usage

```bash
uv run examples/execute_indicators.py \
    --dataset <path-to-csv> \
    --config <path-to-config-json> \
    [--out <output-directory>] \
    [--mode auto|manual]
```

### Arguments

| Argument    | Required | Description                                          |
| ----------- | -------- | ---------------------------------------------------- |
| `--dataset` | Yes      | Path to the raw CSV event log file                   |
| `--config`  | Yes      | Path to `dataset_configs.json`                       |
| `--out`     | No       | Output directory (default: `out_<dataset_name>/`)    |
| `--mode`    | No       | `auto` (default) or `manual` for indicator arguments |

### Argument Modes

**Auto mode** (default): Automatically samples values from the formatted event log to populate indicator arguments. Great for quick exploration.

```bash
uv run examples/execute_indicators.py \
    --dataset examples/datasets/production.csv \
    --config examples/dataset_configs.json \
    --mode auto
```

**Manual mode**: Uses values explicitly defined in `dataset_configs.json`. Useful for testing specific scenarios.

```bash
uv run examples/execute_indicators.py \
    --dataset examples/datasets/bpi-challenge-2013-incidents_100.csv \
    --config examples/dataset_configs.json \
    --mode manual
```

---

## Configuration File

The `dataset_configs.json` file contains column mappings and settings for each dataset:

```json
{
  "production.csv": {
    "case_id_key": "Case ID",
    "activity_key": "Activity",
    "timestamp_key": "Complete Timestamp",
    "start_timestamp_key": "Start Timestamp",
    "total_cost_key": "Cost",
    "separator": ",",
    "date_format": null,
    "dayfirst": true,
    "indicator_arguments": {
      "case_id": "Case 1",
      "activity_name": "Activity A",
      "aggregation_mode": "sgl"
    }
  }
}
```

### Configuration Fields

**Column Mappings** (map your CSV columns to standard names):

- `case_id_key`: Case identifier column
- `activity_key`: Activity name column
- `timestamp_key`: Timestamp column (or end timestamp for production format)
- `start_timestamp_key`: Start timestamp column (production format only)
- `lifecycle_type_key`: Lifecycle transition column (derivable/explicit formats)
- `instance_key`: Instance ID column (explicit format only)
- `total_cost_key`: Cost column
- `human_resource_key`: Resource/performer column

**Format Settings**:

- `separator`: CSV delimiter (default: `,`)
- `date_format`: Timestamp format string (default: auto-detect)
- `dayfirst`: Whether dates are DD/MM/YYYY format (default: `true`)

**Indicator Arguments** (for manual mode):

- `case_id`, `case_ids`: Specific cases to analyze
- `activity_name`, `activity_a`, `activity_b`: Activities for analysis
- `aggregation_mode`: `"sgl"` or `"sum"` for cost calculations
- See `IndicatorArguments` in the [Usage Guide](usage.md#indicatorarguments-reference) for all options

---

## Output Files

Each execution generates three files in the output directory:

| File                      | Description                                                |
| ------------------------- | ---------------------------------------------------------- |
| `formatted_<dataset>.csv` | Normalized explicit interval event log                     |
| `results_<dataset>.csv`   | Detailed indicator calculation results                     |
| `summary_<dataset>.csv`   | Summary showing success rates by dimension and granularity |

### Results File Structure

The results CSV contains:

| Column           | Description                                  |
| ---------------- | -------------------------------------------- |
| `dimension`      | time, cost, quality, flexibility, or general |
| `granularity`    | activities, cases, groups, or instances      |
| `indicator_name` | Name of the indicator function               |
| `status`         | "Success" or error description               |
| `result`         | Calculated value (or None if failed)         |
| `error_message`  | Details if calculation failed                |

### Summary File Structure

The summary shows success rates:

- **Relevant attributes**: How many standard columns exist in your log
- **Dimension columns**: Success rate for each dimension
- **Granularity columns**: Success rate for each granularity level
- **Overall**: Total success rate

---

## Adding Your Own Dataset

1. Place your CSV file in `examples/datasets/`

2. Add configuration to `dataset_configs.json`:

   ```json
   {
     "my_dataset.csv": {
       "case_id_key": "CaseID",
       "activity_key": "Activity",
       "timestamp_key": "Timestamp",
       "separator": ",",
       "dayfirst": false
     }
   }
   ```

3. Run the indicators:

   ```bash
   uv run examples/execute_indicators.py \
       --dataset examples/datasets/my_dataset.csv \
       --config examples/dataset_configs.json
   ```

---

## Example Output

Running the production dataset:

```bash
$ uv run examples/execute_indicators.py \
    --dataset examples/datasets/production.csv \
    --config examples/dataset_configs.json

======================================================================
PROCESS PERFORMANCE INDICATORS - UNIFIED EXECUTION
======================================================================
Dataset: examples/datasets/production.csv
Config: examples/dataset_configs.json
Output: examples/out_production
======================================================================

STEP 1: Loading configuration...
✓ Loaded configuration for: production.csv

STEP 2: Loading and formatting event log...
✓ Formatted log saved to examples/out_production/formatted_production.csv
  Cases: 6
  Activities: 5
  Activity instances: 27

STEP 3: Setting up indicator arguments...
Using auto-sampling approach (review sampled values below)

STEP 4: Running indicators...
Processing indicators: 100%|██████████| 250/250

✓ Results saved to examples/out_production/results_production.csv

STEP 5: Generating summary...
✓ Summary saved to examples/out_production/summary_production.csv

======================================================================
DONE! Check the output files for your results:
======================================================================
```
