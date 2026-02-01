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


# --- Configuration / Package Lists ---
APT_PACKAGES=(
    tree 
    net-tools 
    python3 
    python3-pip 
    python3.10-venv 
    curl 
    xca 
    x11-common 
    lsof
)

PIP_PACKAGES=(
    pandas 
    flask 
    datetime 
    pyopenssl 
    gunicorn
)



export DEBIAN_FRONTEND=noninteractive

pending "Updating package lists..."
sudo apt-get update -y > /dev/null 2>&1 && success "Lists updated" || fail "Apt update failed"


pending "Installing system dependencies..."
# Use "${APT_PACKAGES[@]}" to expand the list correctly
if sudo apt-get install -y -qq "${APT_PACKAGES[@]}" > /dev/null 2>&1; then
    success "System packages installed: ${APT_PACKAGES[*]}"
else
    fail "Failed to install system packages."
fi


pending "Installing Python libraries..."
if pip3 install --upgrade --quiet "${PIP_PACKAGES[@]}"; then
    success "Python libraries installed: ${PIP_PACKAGES[*]}"
else
    pending "pip3 failed, trying python3 -m pip..."
    if python3 -m pip install --upgrade --quiet "${PIP_PACKAGES[@]}"; then
        success "Python libraries installed via module."
    else
        fail "Python library installation failed."
    fi
fi
