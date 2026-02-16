#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }
[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"

ENVIRONMENT="%ENVIRONMENT_PATH%"
source $ENVIRONMENT || fail "Failure in enviroment"
NGINX_CONF="/etc/nginx/sites-enabled/reverse-proxy"

pending "Deleting old nginx conf..."

if [ -e "$NGINX_CONF" ]; then
  rm -f "$NGINX_CONF" \
    && success "Deleted old nginx conf: $NGINX_CONF" \
    || warn "Failed to delete nginx conf: $NGINX_CONF"
else
  success "No old nginx conf found at: $NGINX_CONF"
fi

service nginx reload && success "Nginx reload" || warn "Problem on nginx reload"


pending "Cleaning up processes for $SERVICE_USER on port ${INTERNAL_PORT}"

TARGET_PIDS=$(sudo fuser ${INTERNAL_PORT}/tcp 2>/dev/null)

if [ -n "$TARGET_PIDS" ]; then
    for pid in $TARGET_PIDS; do
        cmd_name=$(ps -p $pid -o comm=)

        if [[ "$cmd_name" == *"python"* ]] || [[ "$cmd_name" == *"gunicorn"* ]]; then
            sudo kill -9 $pid
            success "Killed $cmd_name (PID: $pid) on port ${INTERNAL_PORT}"
        else
            echo "Skipping process '$cmd_name' (PID: $pid) to protect connection."
        fi
    done
else
    success "Port ${INTERNAL_PORT} is already clear."
fi


pending "Removing cron jobs for ${SERVICE_USER} containing: ${JOB_MATCH}"
CRON_FILE="/etc/cron.d/checklist-auto-update-demo"
rm $CRON_FILE || warn "Could not remove $CRON_FILE, might not exist"
ls $CRON_FILE && success "CRON JOB File does not exist" || warn "CRON JOB File still remains"
success "Clean Script finished"