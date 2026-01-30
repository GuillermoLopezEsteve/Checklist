#!/usr/bin/env bash

if [ -z "${BASH_VERSION:-}" ]; then
  printf '\033[31mERROR:\033[0m This script must be run with bash\n' >&2
  printf 'Run it as: bash %s\n' "$0" >&2
  exit 1
fi

bash requirements

# --- Configuration ---
DEFAULT_BRANCH="main"
BRANCH="$DEFAULT_BRANCH"
TEST_MODE=false
PROJECT_DIR=$(pwd)

# --- Cleanup Function (Triggered by Ctrl+C) ---
cleanup() {
    echo ""
    printf '\033[33mCtrl + C Detected Cleaning Enviroment user\033[0m\n'

    echo "Removing Cron Job..."
    (crontab -l 2>/dev/null | grep -v "scripts/class") | crontab -

    echo "Stopping Flask Application..."
    pkill -f "flask run" || true
    pkill -f "python index.py" || true

    echo "Cleanup complete. Exiting."
    exit 0
}

# Register the trap: When SIGINT (Ctrl+C) is received, run 'cleanup'
trap cleanup SIGINT

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash ${BASE_DIR}/scripts/launch_cron.sh


# --- 3. Virtual Environment & Dependencies ---
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# --- 5. Launch Flask App ---
echo "--- Launching Flask Application ---"

pkill -f "flask run" || true
pkill -f "python index.py" || true

python scripts/class/excel.py
# Run in background (&), but we track the PID
FLASK_PID=$!

#nohup python app.py > log_app 2>&1
python app.py
