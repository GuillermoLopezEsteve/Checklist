#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }
[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Cleanup Function (Triggered by Ctrl+C) ---
cleanup() {
    echo ""
    printf '\033[33mCtrl + C Detected Cleaning Enviroment user\033[0m\n'

    pending "Executing clean enviroment script"
    bash ${BASE_DIR}/clean.sh \
        && success "Enviroment clean" \
        || fail "Could NOT Complete Enviroment clean, check if something might be running"
    echo "Cleanup complete. Exiting."
    exit 0
}
trap cleanup SIGINT

LOG_DIR="$BASE_DIR/logs"

pending "Creating logs directory if it doesnt exist"

if [ -d "$LOG_DIR" ]; then
    success "Logs directory exists"
else
    mkdir -p "$LOG_DIR" \
        && success "Logs directory created successfully" || fail "Unable to create directory"
fi

if [ ! -d "venv" ]; then
  pending "Creating virtual environment..."
  python3 -m venv venv \
    && success "Virtual environment created" || fail "Failed to create virtual environment"
fi


FILES=(
    "${BASE_DIR}/.secret/access_key_dev"
    "${BASE_DIR}/.secret/access_key_dev.pub"
    "${BASE_DIR}/.secret/access_key_prod"
    "${BASE_DIR}/.secret/access_key_prod.pub"
)

pending "Checking .secret/ keys for required cron jobs init"

for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        fail "Required file missing: $FILE"
    fi
done

pending "Launching cron jobs..."
bash "${BASE_DIR}/scripts/launch_cron.sh" \
  && success "Cron jobs launched successfully" || fail "Failed to launch cron jobs"


INTERNAL_PORT=8443  # If changed, update config/proxy.conf accordingly

pending "Trying to clean enviroment..."
if [ -f "${BASE_DIR}/clean.sh" ]; then
    pending "Executing clean enviroment script"
    bash ${BASE_DIR}/clean.sh \
        && success "Enviroment clean" \
        || fail "Failure on cleaning enviroment."
else
    fail "No clean.sh found"
fi

pending "Launching Proxy..."
if [ -f "${BASE_DIR}/proxy.sh" ]; then
    pending "Executing proxy script"
    bash ${BASE_DIR}/proxy.sh \
        && success "Proxy running" \
        || fail "Failure on proxy startup"
else
    fail "No proxy script"
fi


pending "Launching Gunicorn..."

PID_FILE="$LOG_DIR/gunicorn.pid"
LOG_FILE="$LOG_DIR/app.log"

nohup gunicorn app:app \
  --bind 127.0.0.1:8443 \
  --workers 4 --threads 2 --timeout 60 \
  --pid "$PID_FILE" \
  > "$LOG_FILE" 2>&1 &

pending "Waiting 5 seconds for start up"
sleep 5

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  success "Gunicorn started (PID $(cat "$PID_FILE"))"
else
  fail "Gunicorn failed to start — check $LOG_FILE"
fi

success "Gunicorn PID in $PID_FILE"
success "Gunicorn LOGS in $LOG_FILE"

