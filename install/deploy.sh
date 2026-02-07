#!/usr/bin/env bash
set -e

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }
[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"
[[ $EUID -eq 0 ]] || fail "This script must be run as sudo"

ENVIRONMENT="%ENVIRONMENT_PATH%"
source $ENVIRONMENT || fail "Failure in enviroment"

LOCAL_CONF="${RUNTIME_DIR}/config/proxy.conf"
SECRET_DIR="${RUNTIME_DIR}/.secret"
NGINX_LINK="/etc/nginx/sites-enabled/reverse-proxy"

FILES=(
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_DEV"
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_DEV.pub"
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_PROD"
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_PROD.pub"
    "${RUNTIME_DIR}/config/demos.json"
    "${RUNTIME_DIR}/config/servers.json"
    "${RUNTIME_DIR}/config/tasks.json"
)

pending "Checking .secret/ keys for required cron jobs init"
pending "Checking config for json files"
for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        fail "Required file missing: $FILE"
    fi
done


CRON="${RUNTIME_DIR}/install/launch_cron.sh"
success "Needed secret files are available"
bash "${CRON}" && success "Cron jobs launched successfully" || fail "Failed to launch cron jobs"


pending "Checking if proxy conf exists in $NGINX_LINK"

if [[ -f "$NGINX_LINK" ]]; then
    success "Nginx conf exists"
else
    warn "Nginx conf $LOCAL_CONF"
    pending "Trying to set up proxy conf"

    cp "$LOCAL_CONF" "/etc/nginx/sites-available/reverse-proxy" \
        && success "Config copied to sites-available" || warn "Failed to copy config to sites-available"

    ln -sf /etc/nginx/sites-available/reverse-proxy "$NGINX_LINK" \
        && success "Symlink created" || warn "Failed to create symbolic link"

    pending "Trying to disable default Nginx site"
    if [[ -L /etc/nginx/sites-enabled/default ]]; then
        rm /etc/nginx/sites-enabled/default \
            && success "Default site disabled" || warn "Could not remove default link"
    fi

    systemctl restart nginx \
        && success "Nginx restarted successfully" || warn "Nginx service failed to restart"
fi


pending "Launching Gunicorn..."

sudo -u ${SERVICE_USER} -- test -x  ${RUNTIME_DIR}/venv/bin/gunicorn \
  && success "OK: gunicorn exists/executable" \
  || fail "NO: missing or not executable"

sudo -u ${SERVICE_USER} -- ${RUNTIME_DIR}/venv/bin/gunicorn app:app 12 \
  --bind 127.0.0.1:8443 \
  --workers 4 --threads 2 --timeout 60
