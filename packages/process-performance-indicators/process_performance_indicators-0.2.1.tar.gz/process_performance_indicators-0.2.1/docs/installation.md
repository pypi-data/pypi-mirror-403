# Installation

## From PyPI

=== "uv (Recommended)"

    [uv](https://docs.astral.sh/uv/) is a fast Python package manager. Install the package with:

    ```bash
    uv add process-performance-indicators
    ```

    Or if you're not using a uv project:

    ```bash
    uv pip install process-performance-indicators
    ```

=== "pip"

    ```bash
    pip install process-performance-indicators
    ```

## From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/nicoabarca/process-performance-indicators.git
cd process-performance-indicators
```

=== "uv"

    ```bash
    uv sync --dev
    ```

=== "pip"

    ```bash
    pip install -e .
    ```

## Requirements

- Python 3.10 or higher
- pandas >= 2.2.3
- tqdm >= 4.67.1

## Verifying Installation

```python
import process_performance_indicators as ppi

# Check available exports
print(dir(ppi))
```

You should see exports like `event_log_formatter`, `run_indicators`, `StandardColumnMapping`, etc.
