#!/bin/bash

# Get the project root directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Call the Python generator directly with system python3
# We pass the config.yaml path as the argument
python3 "$PROJECT_DIR/scripts/test/launcher.py" "$PROJECT_DIR/config/test.yaml"