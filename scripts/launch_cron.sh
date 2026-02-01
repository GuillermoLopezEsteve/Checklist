#!/usr/bin/env bash

GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

fail() {
  echo -e "${RED}[ERROR  ] $NC$1"
  exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $NC$1"
}

pending() {
  echo -e "${YELLOW}[TRYING ] $NC$1"
}

if [ -z "${BASH_VERSION:-}" ]; then
    fail "Must be runned as bash"
fi

CURRENT_USER=$(whoami)
JOB_KEYWORD="prod/launcher.py"

pending "Searching for old cron jobs containing: ${JOB_KEYWORD}"

EXISTING_JOBS=$(crontab -l 2>/dev/null | grep "$JOB_KEYWORD")

if [ -z "$EXISTING_JOBS" ]; then
    success "No old cron jobs found for user ${CURRENT_USER}."
else
    COUNT=$(echo "$EXISTING_JOBS" | wc -l)
    pending "Found ${COUNT} matching job(s). Attempting to delete..."
    if crontab -l | grep -v "$JOB_KEYWORD" | crontab -; then
        success "Successfully deleted ${COUNT} cron job(s) for ${CURRENT_USER}."
    else
        fail "Failed to update crontab. Permission issue?"
    fi
fi

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

FILES=(
    "$SCRIPTPATH/../config/servers.json"
    "$SCRIPTPATH/../config/tasks.json"
    "$SCRIPTPATH/../config/demos.json"
    "$SCRIPTPATH/../config/groups.json"
)

pending "Checking for required configuration JSON files..."

for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        fail "Required file missing: $FILE"
    fi
done

success "All configuration files found."
pending "Adding new cron job for launcher.py..."
LAUNCHER_CMD="*/5 * * * * python3 $SCRIPTPATH/prod/launcher.py ${FILES[0]} ${FILES[1]} ${FILES[2]} ${FILES[3]}"
CURRENT_CRON=$(crontab -l 2>/dev/null)

if echo "$CURRENT_CRON" | grep -Fq "$LAUNCHER_CMD"; then
    success "Cron job already exists. No changes made."
else
    # 3. Append the new job to the existing ones and re-import
    if (echo "$CURRENT_CRON"; echo "$LAUNCHER_CMD") | crontab -; then
        success "New cron job added to run every minute."
    else
        fail "Failed to update crontab."
    fi
fi
