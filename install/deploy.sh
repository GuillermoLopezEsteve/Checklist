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

for v in RUNTIME_DIR SERVICE_USER N_GROUPS; do
  [[ -n "${!v:-}" ]] || fail "$v is required"
done
id $SERVICE_USER &>/dev/null || fail "User '$SERVICE_USER' does not exist"
[[ $N_GROUPS =~ ^[+-]?[0-9]+$ ]] || fail "N_GROUPS is not a number"
[[ -d "$RUNTIME_DIR" ]] || fail "$RUNTIME_DIR does not exist"
sudo -u $SERVICE_USER test -r $RUNTIME_DIR || echo "$SERVICE_USER cannot read $RUNTIME_DIR"

success "Environment setup correct"

SECRET_DIR="${RUNTIME_DIR}/.secret"
NGINX_LINK="/etc/nginx/sites-enabled/reverse-proxy"
LOCAL_CONF="${RUNTIME_DIR}/config/proxy.conf"

FILES=(
    "${SECRET_DIR}/ACCESS_KEY_DEV" "${SECRET_DIR}/ACCESS_KEY_PROD" "${SECRET_DIR}/GOOGLE_CLIENT_ID" "${SECRET_DIR}/GOOGLE_CLIENT_SECRET"
    "${RUNTIME_DIR}/config/demos.json" "${RUNTIME_DIR}/config/tasks.json" "${RUNTIME_DIR}/scripts/launcher.py" "${RUNTIME_DIR}/scripts/src/myExcel.py"
)

pending "Checking .secret/ keys for required cron jobs init and Checking config for json files"
for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        fail "Required file missing: $FILE"
    fi
done

CRON_LOG="${RUNTIME_DIR}/logs/launcher.log"
touch "${CRON_LOG}"
chown ${SERVICE_USER}:${SERVICE_USER} "${CRON_LOG}"

L_COMMAND="${RUNTIME_DIR}/venv/bin/python ${RUNTIME_DIR}/scripts/launcher.py"

LAUNCHER_CMD="*/2 * * * * ${SERVICE_USER} ${L_COMMAND} ${RUNTIME_DIR}/config/demos.json >> ${CRON_LOG} 2>&1"
CRON_FILE="/etc/cron.d/checklist-auto-update-demo"
{
  echo "SHELL=/bin/bash"
  echo "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  echo "$LAUNCHER_CMD"
} > "$CRON_FILE" || fail "Failure to write cron job"

chmod 0644 "$CRON_FILE" || fail "Failed to set permissions on $CRON_FILE"
success "Cron File setup"

if [[ -f "$NGINX_LINK" ]]; then
    success "Nginx conf exists"
else
    warn "Setting up Nginx conf from $LOCAL_CONF"

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
touch ${RUNTIME_DIR}/logs/gunicorn_error.log ${RUNTIME_DIR}/logs/gunicorn_access.log || fail "Could not create files"
chown ${SERVICE_USER}:${SERVICE_USER} ${RUNTIME_DIR}/logs/gunicorn_error.log || fail "Could not create files"
chown ${SERVICE_USER}:${SERVICE_USER} ${RUNTIME_DIR}/logs/gunicorn_access.log || fail "Could not create files"

sudo -u ${SERVICE_USER} -- test -x  ${RUNTIME_DIR}/venv/bin/gunicorn \
  && success "OK: gunicorn exists/executable" \
  || fail "NO: missing or not executable"

sudo -u ${SERVICE_USER} -- ${RUNTIME_DIR}/venv/bin/gunicorn app:app ${N_GROUPS} \
  --bind 127.0.0.1:8443 \
  --workers 4 --threads 2 --timeout 60 \
  --error-logfile "${RUNTIME_DIR}/logs/gunicorn_error.log" \
  --access-logfile "${RUNTIME_DIR}/logs/gunicorn_access.log"
