#!/usr/bin/env bash
set -e

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }
[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"

ENVIRONMENT="%ENVIRONMENT_PATH%"
source $ENVIRONMENT || fail "Failure in enviroment"

JOB_REGEX='(python3?|/usr/bin/python3).*launcher\.py|launcher\.py'

pending "Searching for old cron jobs for user ${SERVICE_USER} matching regex: ${JOB_REGEX}"

CURRENT_CRON="$(crontab -u "$SERVICE_USER" -l 2>/dev/null || true)"
EXISTING_JOBS="$(printf '%s\n' "$CURRENT_CRON" | grep -E "$JOB_REGEX" || true)"

if [ -z "$EXISTING_JOBS" ]; then
    success "No old cron jobs found for user ${SERVICE_USER}."
else
    COUNT="$(printf '%s\n' "$EXISTING_JOBS" | wc -l | tr -d ' ')"
    pending "Found ${COUNT} matching job(s). Attempting to delete..."

    UPDATED_CRON="$(printf '%s\n' "$CURRENT_CRON" | grep -Ev "$JOB_REGEX" || true)"

    if printf '%s\n' "$UPDATED_CRON" | crontab -u "$SERVICE_USER" -; then
        success "Successfully deleted ${COUNT} cron job(s) for ${SERVICE_USER}."
    else
        fail "Failed to update crontab for ${SERVICE_USER}. Permission issue?"
    fi
fi


FILES=(
    "$RUNTIME_DIR/scripts/launcher.py"
    "$RUNTIME_DIR/config/servers.json"
    "$RUNTIME_DIR/config/tasks.json"
    "$RUNTIME_DIR/config/demos.json"
    "$RUNTIME_DIR/scripts/launcher.py"
    "$RUNTIME_DIR/scripts/src/myExcel.py"
    "$RUNTIME_DIR/scripts/src/myTasks.py"
)

pending "Checking for required configuration JSON files..."

for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        fail "Required file missing: $FILE"
    fi
done
success "All configuration files found."

pending "Adding new cron job for launcher.py..."

LAUNCHER="$RUNTIME_DIR/scripts/launcher.py"
DATA_CONFIG="$RUNTIME_DIR/config"
chmod +x "$LAUNCHER" || fail "Failure to make $LAUNCHER executable"

SERV_CONFIG="${DATA_CONFIG}/servers.json"
TASK_CONFIG="${DATA_CONFIG}/tasks.json"
DEMO_CONFIG="${DATA_CONFIG}/demos.json"
CRON_LOG="${RUNTIME_DIR}/logs/launcher.log"

LAUNCHER_CMD="* * * * * ${RUNTIME_DIR}/venv/bin/python ${LAUNCHER} ${SERV_CONFIG} ${TASK_CONFIG} ${DEMO_CONFIG} >> ${CRON_LOG} 2>&1"

CURRENT_CRON="$(crontab -u "$SERVICE_USER" -l 2>/dev/null || true)"

if echo "$CURRENT_CRON" | grep -Fq "$LAUNCHER_CMD"; then
    success "Cron job already exists for $SERVICE_USER. No changes made."
else
    if (echo "$CURRENT_CRON"; echo "$LAUNCHER_CMD") | crontab -u "$SERVICE_USER" -; then
        success "New cron job added for $SERVICE_USER (every 5 minutes)."
    else
        fail "Failed to update crontab for $SERVICE_USER."
    fi
fi

success "LAUNCHING CRON JOB CORRECT"
