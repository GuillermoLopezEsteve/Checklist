#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }

[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"
[[ $EUID -eq 0 ]] || fail "This script must be run as sudo"


DEPLOY_ARGS=()

SERVICE_NAME="checklist"
SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"
RUNTIME_DIR="/etc/${SERVICE_NAME}"
SERVICE_USER="$SERVICE_NAME"
SERVICE_GROUP="$SERVICE_NAME"

ORIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[[ -n "$RUNTIME_DIR" && "$RUNTIME_DIR" == "/etc/$SERVICE_NAME" ]] \
  && ( [[ -d "$RUNTIME_DIR" ]] \
       && ( pending "Removing $RUNTIME_DIR" \
            && rm -rf "$RUNTIME_DIR" \
            && success "$RUNTIME_DIR removed" || fail "Failed to remove $RUNTIME_DIR" ) || warn "$RUNTIME_DIR does not exist" ) || fail "Refusing to delete unsafe path: '$RUNTIME_DIR'"

pending "Copying $ORIG_DIR to $RUNTIME_DIR"
cp -r $ORIG_DIR ${RUNTIME_DIR} && success "Copying to runtime directory ${RUNTIME_DIR}" || fail "Copying to runtime directory ${RUNTIME_DIR}"

TEMPLATE="${RUNTIME_DIR}/config/checklist.service"
DEPLOY="${RUNTIME_DIR}/install/deploy.sh"
CLEAN="${RUNTIME_DIR}/install/clean.sh"
REQUIREMENTS="${RUNTIME_DIR}/install/requirements.sh"
LOG_DIR="${RUNTIME_DIR}/logs"
PROXY="${RUNTIME_DIR}/install/proxy.sh"
CRON="${RUNTIME_DIR}/install/proxy.sh"
TIMEZONE="${RUNTIME_DIR}/install/timezone.sh"

pending "Checking needed files"

[[ -f "$DEPLOY" ]]       && success "File exists: $DEPLOY" || fail "File not found: $DEPLOY"
[[ -f "$CLEAN" ]]        && success "File exists: $CLEAN" || fail "File not found: $CLEAN"
[[ -f "$TEMPLATE" ]]     && success "File exists: $TEMPLATE" || fail "File not found: $TEMPLATE"
[[ -f "$REQUIREMENTS" ]] && success "File exists: $REQUIREMENTS" || fail "File not found: $REQUIREMENTS"
[[ -f "$PROXY" ]]        && success "File exists: $PROXY" || fail "File not found: $PROXY"
[[ -f "$CRON" ]]         && success "File exists: $CRON" || fail "File not found: $CRON"
[[ -f "$TIMEZONE" ]]     && success "File exists: $TIMEZONE" || fail "File not found: $TIMEZONE"

pending "Trying to set up Timezone"
if [[ "$1" == "-t" && -n "$TIMEZONE" && -f "$TIMEZONE" ]]; then
    bash "$TIMEZONE" || fail "Failure in TimeZone"
else
    warn "TimeZone not  set up call with -t"
fi
success "TIMEZONE setup to: $(date +'%Z')"


LOG_DIR="$BASE_DIR/logs"

pending "Creating logs directory if it doesnt exist"

[[ -d "$LOG_DIR" ]] \
  && success "Logs directory exists" \
  || ( mkdir -p "$LOG_DIR" && chown "$SERVICE_USER":"$SERVICE_GROUP" "$LOG_DIR" \
       && success "Logs directory created" || fail "Unable to create logs directory" )


pending "Making requirements executables"
chmod +x ${REQUIREMENTS} && success "Requirements is now executable" || fail "Failed to make requirements executable"
pending "Installing dependencies..."
bash $REQUIREMENTS && success "Dependencies installed successfully" || fail "Dependency installation failed"

warn "This service will run as root"
TARGET_USER="root"

warn "User $SERVICE_USER needs acces to files"

id "$SERVICE_USER" &>/dev/null && success "User '$SERVICE_USER' exists" || fail "User '$SERVICE_USER' does not exist"

sudo -u checklist -- test -r "$RUNTIME_DIR" && sudo -u checklist -- test -w "$RUNTIME_DIR" \
    && success "$SERVICE_USER has access to $RUNTIME_DIR" || fail "$SERVICE_USER does not have access to $RUNTIME_DIR"

pending "Launching Proxy..."
pending "Executing proxy script"
bash ${PROXY}  && success "Proxy running" || fail "Failure on proxy startup"



pending "Making tmp copy and replacing placeholders for script variables"
grep -q '%USERNAME%' "$TEMPLATE" || fail "%USERNAME% missing in template"
grep -q '%DEPLOY%'   "$TEMPLATE" || fail "%DEPLOY% missing in template"
grep -q '%CLEAN%'    "$TEMPLATE" || fail "%CLEAN% missing in template"

tmp="$(mktemp)" || fail "mktemp failed"

sed \
  -e "s|%USERNAME%|$TARGET_USER|g" \
  -e "s|%DEPLOY%|$DEPLOY|g" \
  -e "s|%CLEAN%|$CLEAN|g" \
  "$TEMPLATE" > "$tmp" || fail "Template render failed"

success "Created tmp copy"

pending "Reinstalling ${SERVICE_NAME} systemd service"

pending "Checking for old ${SERVICE_NAME}.service"
systemctl list-unit-files | grep -q "^${SERVICE_NAME}\.service" \
  && systemctl stop "$SERVICE_NAME" && systemctl disable "$SERVICE_NAME" \
  && rm -f "$SERVICE" && systemctl daemon-reload \
  && warn "Old service detected and removed" \
  || success "No service detected"

pending "Making scripts executable"
chmod +x "$DEPLOY" "$CLEAN" && success "Scripts made executable" || fail "chmod failed"

pending "Installing systemd service"
install -m 0644 "$tmp" "$SERVICE" && success "Service installed" || fail "install failed"
systemctl daemon-reload && success "Daemon reloaded" || fail "daemon-reload failed"
systemctl enable checklist && success "Service enabled" || fail "enable failed"
systemctl restart checklist && success "Service started" || fail "start failed"

FILES=(
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_DEV"
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_DEV.pub"
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_PROD"
    "${RUNTIME_DIR}/.secret/ACCESS_KEY_PROD.pub"
)

pending "Checking .secret/ keys for required cron jobs init"

for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        fail "Required file missing: $FILE"
    fi
done

warn "Cron jobs launcher will be executed in deploy, checkout status"
