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

NGINX_CONF="/etc/nginx/sites-enabled/reverse-proxy"
INTERNAL_PORT=8443
CURRENT_USER=$(whoami)

pending "Deleting old nginx conf..."

if [ -e "$NGINX_CONF" ]; then
  sudo rm -f "$NGINX_CONF" \
    && success "Deleted old nginx conf: $NGINX_CONF" \
    || fail "Failed to delete nginx conf: $NGINX_CONF"
else
  success "No old nginx conf found at: $NGINX_CONF"
fi


pending "Cleaning up processes for ${CURRENT_USER} on port ${INTERNAL_PORT}..."

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
