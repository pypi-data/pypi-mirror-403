#!/usr/bin/env bash

# Run All Examples Script
#
# Usage:
#   ./run_all_examples.sh           # Run with auto-sampled arguments (default)
#   ./run_all_examples.sh --mode auto    # Same as above
#   ./run_all_examples.sh --mode manual  # Use manually configured arguments from JSON

set -e  # Exit on error

# Parse command line arguments
MODE="auto"
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--mode auto|manual]"
            exit 1
            ;;
    esac
done

# Validate mode
if [[ "$MODE" != "auto" && "$MODE" != "manual" ]]; then
    echo "Invalid mode: $MODE"
    echo "Valid modes: auto, manual"
    exit 1
fi

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track results
TOTAL=0
SUCCESS=0
FAILED=0
FAILED_EXAMPLES=()

echo "======================================================================"
echo "Running All Indicator Examples"
echo "======================================================================"
echo -e "Mode: ${BLUE}${MODE}${NC}"
echo ""

# Get the script directory (examples directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Config file path
CONFIG_FILE="${SCRIPT_DIR}/dataset_configs.json"

# Define datasets as array of "name:path" pairs
DATASETS=(
    "atomic_log:datasets/atomic_event_log.csv"
    "derivable_interval_log:datasets/derivable_interval_event_log.csv"
    "explicit_interval_log:datasets/explicit_interval_event_log.csv"
    "uniquely_matched_derivable_interval_log:datasets/timestamp_unique_derivable_interval_event_log.csv"
    "production:datasets/production.csv"
    "bpi_challenge_2013_incidents:datasets/bpi-challenge-2013-incidents_100.csv"
    "bpi_challenge_2017:datasets/bpi-challenge-2017_100.csv"
    "it_incident:datasets/it-incident_100.csv"
    "italian_help_desk:datasets/italian-help-desk_100.csv"
)

# Function to run a single example
run_example() {
    local example_name=$1
    local dataset_file=$2
    
    local dataset_path="${SCRIPT_DIR}/${dataset_file}"
    
    if [ ! -f "${dataset_path}" ]; then
        echo -e "${YELLOW}⊘ Skipping ${example_name}: dataset file not found at ${dataset_path}${NC}"
        return
    fi
    
    TOTAL=$((TOTAL + 1))
    
    echo ""
    echo "======================================================================"
    echo -e "${BLUE}[${TOTAL}] Running: ${example_name}${NC}"
    echo "======================================================================"
    
    # Run unified execute_indicators.py script from project root
    if cd "${PROJECT_ROOT}" && uv run examples/execute_indicators.py --dataset "${dataset_path}" --config "${CONFIG_FILE}" --mode "${MODE}"; then
        SUCCESS=$((SUCCESS + 1))
        echo -e "${GREEN}✓ ${example_name} completed successfully${NC}"
    else
        FAILED=$((FAILED + 1))
        FAILED_EXAMPLES+=("${example_name}")
        echo -e "${RED}✗ ${example_name} failed${NC}"
    fi
    
    # Return to project root
    cd "${PROJECT_ROOT}"
}

# Run all examples
for dataset_entry in "${DATASETS[@]}"; do
    IFS=':' read -r example_name dataset_file <<< "$dataset_entry"
    run_example "$example_name" "$dataset_file"
done

# Print summary
echo ""
echo "======================================================================"
echo "Summary"
echo "======================================================================"
echo -e "Total examples: ${TOTAL}"
echo -e "${GREEN}Successful: ${SUCCESS}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"

if [ ${FAILED} -gt 0 ]; then
    echo ""
    echo "Failed examples:"
    for failed_example in "${FAILED_EXAMPLES[@]}"; do
        echo -e "  ${RED}✗ ${failed_example}${NC}"
    done
    echo ""
    exit 1
else
    echo ""
    echo -e "${GREEN}✓ All examples completed successfully!${NC}"
    echo ""
    exit 0
fi
