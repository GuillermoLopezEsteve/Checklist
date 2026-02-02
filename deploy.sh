#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }
[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"

BASE_DIR="/etc/checklist/"

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
success "Needed fails are available"
#pending "Launching cron jobs..."
#bash "${BASE_DIR}/scripts/launch_cron.sh" && success "Cron jobs launched successfully" || fail "Failed to launch cron jobs"


pending "Launching Gunicorn..."

sudo -u checklist -- test -x /etc/checklist/venv/bin/gunicorn \
  && success "OK: gunicorn exists/executable" \
  || fail "NO: missing or not executable"

sudo -u checklist -- /etc/checklist/venv/bin/gunicorn app:app \
  --bind 127.0.0.1:8443 \
  --workers 4 --threads 2 --timeout 60
