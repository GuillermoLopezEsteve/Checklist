#!/bin/bash

# --- Configuration ---
DEFAULT_BRANCH="main"
BRANCH="$DEFAULT_BRANCH"
TEST_MODE=false
PROJECT_DIR=$(pwd)

# --- Cleanup Function (Triggered by Ctrl+C) ---
cleanup() {
    echo -e "\n\n!!! CRITICAL: Ctrl+C Detected !!!"
    echo "--- Cleaning up environment ---"

    # 1. Remove the Cron Job
    echo "Removing Cron Job..."
    # We list the crontab, remove any lines containing our script path, and save it back
    (crontab -l 2>/dev/null | grep -v "scripts/server_check") | crontab -

    # 2. Kill the Flask App
    echo "Stopping Flask Application..."
    pkill -f "flask run" || true
    pkill -f "python index.py" || true

    echo "Cleanup complete. Exiting."
    exit 0
}

# Register the trap: When SIGINT (Ctrl+C) is received, run 'cleanup'
trap cleanup SIGINT

# --- Argument Parsing ---
for arg in "$@"; do
    case $arg in
        -t)
            TEST_MODE=true
            shift
            ;;
        *)
            BRANCH=$arg
            ;;
    esac
done

echo "--- Starting Deployment Script (Press Ctrl+C to Stop & Cleanup) ---"

if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
fi

# --- 3. Virtual Environment & Dependencies ---
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Clean old jobs first to prevent duplicates, then add the new one
(crontab -l 2>/dev/null | grep -v "scripts/server_check") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
echo "Cron job active: $CRON_CMD"


# --- 5. Launch Flask App ---
echo "--- Launching Flask Application ---"

pkill -f "flask run" || true
pkill -f "python index.py" || true
# Run in background (&), but we track the PID
FLASK_PID=$!

export FLASK_APP=index.py
export FLASK_ENV=production
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000

nohup python -m flask run > flask_app.log 2>&1 &
FLASK_PID=$!

echo "Flask is running (PID: $FLASK_PID)."
echo "---------------------------------------------------"
echo "Script is now monitoring logs."
echo "PRESS CTRL+C TO STOP FLASK AND DELETE THE CRON JOB."
echo "---------------------------------------------------"

# --- 6. Keep Script Alive ---
# We tail the logs so the script stays running, waiting for your Ctrl+C
tail -f flask_app.log
