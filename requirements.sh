#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }

[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"
[[ $EUID -eq 0 ]] || fail "This script must be run as sudo"

# --- Configuration / Package Lists ---
APT_PACKAGES=(
  tree net-tools python3 python3-pip python3-venv curl xca x11-common lsof
)

PIP_PACKAGES=(
  pandas flask pyOpenSSL gunicorn
)

SERVICE_USER="checklist"
SERVICE_GROUP="checklist"

PREV_OWNER="$(stat -c '%U' "$BASE_DIR")"
export DEBIAN_FRONTEND=noninteractive
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pending "Updating package lists..."
apt-get update -qq && success "Lists updated" || fail "Apt update failed"

pending "Installing system dependencies..."
if sudo apt-get install -y -qq "${APT_PACKAGES[@]}" > /dev/null 2>&1; then
    success "System packages installed: ${APT_PACKAGES[*]}"
else
    fail "Failed to install system packages."
fi


pending "Installing Python libraries for $SERVICE_USER"

pending "Preparing permissions for $SERVICE_USER in $BASE_DIR"

getent group "$SERVICE_GROUP" >/dev/null || groupadd --system "$SERVICE_GROUP" || fail "groupadd failed"
id -u "$SERVICE_USER" >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin -g "$SERVICE_GROUP" "$SERVICE_USER" || fail "useradd failed"

chown -R root:"$SERVICE_GROUP" "$BASE_DIR" || fail "chown base_dir failed"
find "$BASE_DIR" -type d -exec chmod 2775 {} + || fail "chmod dirs failed"
find "$BASE_DIR" -type f -exec chmod 664 {} + || fail "chmod files failed"

success "Permissions OK (root:$SERVICE_GROUP, group-writable)"

read -rp "Add previous owner '$PREV_OWNER' to group '$SERVICE_GROUP'? [Y/n]: " ans
if [[ ! "$ans" =~ ^[Nn]$ ]]; then
  pending "Adding $PREV_OWNER to $SERVICE_GROUP"
  id -nG "$PREV_OWNER" | grep -qw "$SERVICE_GROUP" \
    || usermod -aG "$SERVICE_GROUP" "$PREV_OWNER" \
    && success "$PREV_OWNER added to $SERVICE_GROUP" || fail "Failed to add $PREV_OWNER to $SERVICE_GROUP"
else
  warn "Skipping group membership change"
fi


VENV_DIR="$BASE_DIR/venv"

[[ -d "$VENV_DIR" ]] \
  || ( pending "Creating venv" \
       && sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR" \
       && success "Venv created" || fail "venv failed" )
