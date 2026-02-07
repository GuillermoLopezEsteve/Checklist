#!/usr/bin/env bash
set -e

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }

[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"
[[ $EUID -eq 0 ]] || fail "This script must be run as sudo"


pending "Setting up application..."
pending "Environment setup...."

ORIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ENVIRONMENT="$1"
if [[ -z "$ENVIRONMENT" ]]; then
  ENVIRONMENT="$ORIG_DIR/config.env"
  warn "No config file passed, using the default one: $ENVIRONMENT"
fi

[[ -f "$ENVIRONMENT" ]] && success "File exists: $ENVIRONMENT" || fail "File not found: $ENVIRONMENT"

# shellcheck disable=SC1090
source "$ENVIRONMENT" || fail "Failure loading environment: $ENVIRONMENT"

pending "Checking correct config.env"

for v in RUNTIME_DIR SERVICE_NAME SERVICE_USER SERVICE_GROUP PROXY_SETUP TIME_SETUP SERVICE; do
  [[ -n "${!v:-}" ]] && success "$v found: ${!v}" || fail "$v is required"
done

[[ -n "${RUNTIME_DIR:-}" ]] \
    && success "RUNTIME_DIR found: $RUNTIME_DIR" || fail "RUNTIME_DIR is required"


[[ -n "$RUNTIME_DIR" && "$RUNTIME_DIR" == "/etc/$SERVICE_NAME" ]] \
  && ( [[ -d "$RUNTIME_DIR" ]] \
       && ( pending "Removing $RUNTIME_DIR" \
            && rm -rf "$RUNTIME_DIR" \
            && success "$RUNTIME_DIR removed" || fail "Failed to remove $RUNTIME_DIR" ) || warn "$RUNTIME_DIR does not exist" ) || fail "Refusing to delete unsafe path: '$RUNTIME_DIR'"

pending "Copying $ORIG_DIR to $RUNTIME_DIR"
cp -r $ORIG_DIR ${RUNTIME_DIR} && success "Copying to runtime directory ${RUNTIME_DIR}" || fail "Copying to runtime directory ${RUNTIME_DIR}"

pending "Copying config to $RUNTIME_DIR"
cp "$ENVIRONMENT" "${RUNTIME_DIR}/config.env" || fail "Failed to copy config to runtime dir"

TEMPLATE="${RUNTIME_DIR}/config/checklist.service"
DEPLOY="${RUNTIME_DIR}/install/deploy.sh"
CLEAN="${RUNTIME_DIR}/install/clean.sh"
REQUIREMENTS="${RUNTIME_DIR}/install/requirements.sh"
LOG_DIR="${RUNTIME_DIR}/logs"
PROXY="${RUNTIME_DIR}/install/proxy.sh"
CRON="${RUNTIME_DIR}/install/launch_cron.sh"
TIMEZONE="${RUNTIME_DIR}/install/timezone.sh"
ENVIRONMENT="${RUNTIME_DIR}/config.env"
pending "Checking needed files"

[[ -f "$DEPLOY" ]]       && success "File exists: $DEPLOY" || fail "File not found: $DEPLOY"
[[ -f "$CLEAN" ]]        && success "File exists: $CLEAN" || fail "File not found: $CLEAN"
[[ -f "$TEMPLATE" ]]     && success "File exists: $TEMPLATE" || fail "File not found: $TEMPLATE"
[[ -f "$REQUIREMENTS" ]] && success "File exists: $REQUIREMENTS" || fail "File not found: $REQUIREMENTS"
[[ -f "$PROXY" ]]        && success "File exists: $PROXY" || fail "File not found: $PROXY"
[[ -f "$CRON" ]]         && success "File exists: $CRON" || fail "File not found: $CRON"
[[ -f "$TIMEZONE" ]]     && success "File exists: $TIMEZONE" || fail "File not found: $TIMEZONE"

pending "Trying to set up Timezone"
if [[ ! $TIME_SETUP ]]; then
    bash $TIMEZONE || fail "Failure in TimeZone"
else
    warn "TimeZone not set up call, change via config"
fi
success "TIMEZONE setup to: $(date +'%Z')"


pending "Creating logs directory if it doesnt exist"

[[ -d "$LOG_DIR" ]] \
  && success "Logs directory exists" \
  || ( mkdir -p "$LOG_DIR" && chown "$SERVICE_USER":"$SERVICE_GROUP" "$LOG_DIR" \
       && success "Logs directory created" || fail "Unable to create logs directory" )


pending "Making requirements executables"
chmod +x ${REQUIREMENTS} && success "Requirements is now executable" || fail "Failed to make requirements executable"
pending "Installing dependencies..."
bash $REQUIREMENTS $ENVIRONMENT && success "Dependencies installed successfully" || fail "Dependency installation failed"

warn "This service will run as root"
TARGET_USER="root"

warn "User $SERVICE_USER needs acces to files"

id $SERVICE_USER &>/dev/null && success "User '$SERVICE_USER' exists" || fail "User '$SERVICE_USER' does not exist"

sudo -u checklist -- test -r "$RUNTIME_DIR" && sudo -u checklist -- test -w "$RUNTIME_DIR" \
    && success "$SERVICE_USER has access to $RUNTIME_DIR" || fail "$SERVICE_USER does not have access to $RUNTIME_DIR"

#REPLACING %PLACEHOLDERS% FOR EXACT VARIABLES
pending "Replacing placeholders for deploy and cron and clean"

grep -q '%ENVIRONMENT_PATH%' $CRON   || fail "%ENVIRONMENT_PATH% missing in $CRON"
grep -q '%ENVIRONMENT_PATH%' $DEPLOY || fail "%ENVIRONMENT_PATH% missing in $DEPLOY"
grep -q '%ENVIRONMENT_PATH%' $CLEAN  || fail "%ENVIRONMENT_PATH% missing in $CLEAN"
escape_sed() { printf '%s' "$1" | sed 's/[&|]/\\&/g'; }
ENV_ESCAPED="$(escape_sed "$ENVIRONMENT")"

# ---- CRON ----
tmp_cron="$(mktemp)" || fail "mktemp failed for cron"
sed "s|%ENVIRONMENT_PATH%|$ENV_ESCAPED|g" $CRON > $tmp_cron || fail "Cron environment replacing failed"
mv $tmp_cron $CRON || fail "Failure on mv tmp"

success "Placeholders replaced in $CRON"
# ---- DEPLOY ----
tmp_deploy="$(mktemp)" || fail "mktemp failed for deploy"
sed "s|%ENVIRONMENT_PATH%|$ENV_ESCAPED|g" $DEPLOY > $tmp_deploy || fail "Deploy environment replacing failed"
mv $tmp_deploy $DEPLOY || fail "Failure on mv tmp"

success "Placeholders replaced in $DEPLOY"
# ---- CLEAN ----
tmp_clean="$(mktemp)" || fail "mktemp failed for clean"
sed "s|%ENVIRONMENT_PATH%|$ENV_ESCAPED|g" \
  "$DEPLOY" > "$tmp_clean" || fail "Clean environment replacing failed"
mv "$tmp_clean" "$DEPLOY" || fail "Failure on mv tmp"

success "Placeholders replaced in $CLEAN"
# ---- SERVICE ----
pending "Replacing %placeholders% in service template: $TEMPLATE"
grep -q '%USERNAME%' "$TEMPLATE"         || fail "%USERNAME% missing in template"
grep -q '%DEPLOY%'   "$TEMPLATE"         || fail "%DEPLOY% missing in template"
grep -q '%CLEAN%'    "$TEMPLATE"         || fail "%CLEAN% missing in template"
grep -q '%RUNTIME_DIR%' "$TEMPLATE"      || fail "%RUNTIME_DIR% missing in template"
grep -q '%ENVIRONMENT_PATH%' "$TEMPLATE" || fail "%ENVIRONMENT_PATH% missing in template"

success "Found %PLACEHOLDER% in $TEMPLATE, procceding to substitute"
tmp_service="$(mktemp)" || fail "mktemp failed"
sed \
  -e "s|%USERNAME%|$TARGET_USER|g" \
  -e "s|%DEPLOY%|$DEPLOY|g" \
  -e "s|%CLEAN%|$CLEAN|g" \
  -e "s|%RUNTIME_DIR%|$RUNTIME_DIR|g" \
  -e "s|%ENVIRONMENT_PATH%|$ENVIRONMENT|g" \
  "$TEMPLATE" > "$tmp_service" || fail "Service template placeholder replacement failed"
mv $tmp_service $TEMPLATE || fail "Couldnt copy tmp_service into $TEMPLATE"
success "Created on service placeholder replacement: $TEMPLATE"
pending "Launching Proxy..."
pending "Executing proxy script"

if [[ $PROXY_SETUP ]]; then
    [[ ! -z "${INTERNAL_PORT:-}" ]] && success "INTERNAL_PORT found: $INTERNAL_PORT" || fail "INTERNAL_PORT is needed for PROXY_SETUP"
    pending "Replacing placeholders in proxy.conf"
    PROXY_CONFIG="${RUNTIME_DIR}/config/proxy.conf"
    grep -q '%INTERNAL_PORT%' "$PROXY_CONFIG" || fail "%INTERNAL_PORT% missing in PROXY_CONFIG"
    tmp_proxy="$(mktemp)" || fail "mktemp failed for clean"
    sed "s|%INTERNAL_PORT%|$INTERNAL_PORT|g" \
      "$PROXY_CONFIG" > "$tmp_proxy" || fail "Proxy config replacing failed"
    mv "$tmp_proxy" "$PROXY_CONFIG" || fail "Failure on mv tmp proxy"

    success "Replacing placeholders in proxy.config"
    bash $PROXY $ENVIRONMENT || fail "Failure in proxy setup"
fi

pending "Reinstalling ${SERVICE_NAME} systemd service"

pending "Checking for old ${SERVICE_NAME}.service"
systemctl list-unit-files | grep -q "^${SERVICE_NAME}\.service" \
  && systemctl stop $SERVICE_NAME && systemctl disable $SERVICE_NAME \
  && rm -f $SERVICE && systemctl daemon-reload \
  && warn "Old service detected and removed" \
  || success "No service detected"

pending "Making scripts executable"
chmod +x $DEPLOY $CLEAN && success "Scripts made executable" || fail "chmod failed"

pending "Installing systemd service"
install -m 0644 $TEMPLATE $SERVICE && success "Service installed" || fail "install failed"
systemctl daemon-reload && success "Daemon reloaded" || fail "daemon-reload failed"
systemctl enable checklist && success "Service enabled" || fail "enable failed"
systemctl restart checklist && success "Service started" || fail "start failed"

warn "Cron jobs launcher will be executed in deploy, checkout status in $LOG_DIR or service $SERVICE_NAME status"

pending "Sleeping 10 seconds then checking service status"
sleep 10
systemctl is-active --quiet checklist \
  && success "Service running" \
  || { fail "Service failure"; systemctl status checklist --no-pager; }

