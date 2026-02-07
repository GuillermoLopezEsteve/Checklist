#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }

[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"
[[ $EUID -eq 0 ]] || fail "This script must be run as sudo"

ENVIROMENT=$1
if [[ -z "$ENVIROMENT" ]]; then
  fail "No config file passed"
fi
source $ENVIROMENT || fail "Failure in enviroment"


# --- Configuration / Package Lists ---
APT_PACKAGES=(
  tree net-tools python3 python3-pip python3-venv curl xca x11-common lsof nginx
)

PIP_PACKAGES=(
  pandas flask pyOpenSSL gunicorn
)

export DEBIAN_FRONTEND=noninteractive

pending "Updating package lists..."
apt-get update -qq && success "Lists updated" || fail "Apt update failed"

pending "Installing system dependencies..."
if apt-get install -y -qq "${APT_PACKAGES[@]}" > /dev/null 2>&1; then
    success "System packages installed: ${APT_PACKAGES[*]}"
else
    fail "Failed to install system packages."
fi


pending "Installing Python libraries for $SERVICE_USER"

pending "Preparing permissions for $SERVICE_USER in $RUNTIME_DIR"

getent group "$SERVICE_GROUP" >/dev/null || groupadd --system "$SERVICE_GROUP" || fail "groupadd failed"
id -u "$SERVICE_USER" >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin -g "$SERVICE_GROUP" "$SERVICE_USER" || fail "useradd failed"


[[ -n "$RUNTIME_DIR" && -d "$RUNTIME_DIR" ]] || fail "RUNTIME_DIR not set or missing: '$RUNTIME_DIR'"

chown -R root:"$SERVICE_GROUP" "$RUNTIME_DIR" || fail "chown $RUNTIME_DIR failed"
find "$RUNTIME_DIR" -type d -exec chmod 2775 {} + || fail "chmod dirs failed"
find "$RUNTIME_DIR" -type f -exec chmod 664 {} + || fail "chmod files failed"
success "Permissions OK (root:$SERVICE_GROUP, group-writable)"

VENV_DIR="$RUNTIME_DIR/venv"
pending "Deleting venv"
[[ -n "$VENV_DIR" && "$VENV_DIR" == "$RUNTIME_DIR"/venv ]] || fail "Refusing to delete unsafe path: $VENV_DIR"
[[ -d "$VENV_DIR" ]] && (rm -rf "$VENV_DIR" && success "Venv removed" || fail "Failed to remove venv") || warn "No venv to remove"

[[ -d "$VENV_DIR" ]] \
  || ( pending "Creating venv" \
       && sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR" \
       && success "Venv created" || fail "venv failed" )

pending "Installing Python libraries into venv"
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" -m pip install --no-cache-dir -U --quiet pip setuptools wheel \
  && sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" -m pip install  --no-cache-dir -U --quiet "${PIP_PACKAGES[@]}" \
  && success "Python libraries installed in venv" || fail "pip install failed"
