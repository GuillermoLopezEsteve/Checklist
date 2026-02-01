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

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
LOCAL_CONF="$SCRIPTPATH/config/proxy.conf"
NGINX_LINK="/etc/nginx/sites-enabled/reverse-proxy"

pending "Checking if Nginx is installed..."
if ! command -v nginx >/dev/null 2>&1; then
    fail "Nginx is not installed on this system."
fi

pending "Verifying local configuration file at $LOCAL_CONF..."
if [ ! -f "$LOCAL_CONF" ]; then
    fail "Local config file not found at $LOCAL_CONF"
fi
success "Local config found."

pending "Applying Nginx configuration..."

sudo cp "$LOCAL_CONF" /etc/nginx/sites-available/reverse-proxy || fail "Failed to copy config to sites-available."
sudo ln -sf /etc/nginx/sites-available/reverse-proxy "$NGINX_LINK" || fail "Failed to create symbolic link."

if [ -L /etc/nginx/sites-enabled/default ]; then
    pending "Disabling default Nginx site..."
    sudo rm /etc/nginx/sites-enabled/default \
         && success "Default site disabled." || fail "Could not remove default link."
fi

pending "Testing Nginx configuration syntax..."
if sudo nginx -t >/dev/null 2>&1; then
    success "Nginx configuration syntax is valid."
    pending "Restarting Nginx..."
    if sudo systemctl restart nginx; then
        success "Nginx restarted successfully."
    else
        fail "Nginx syntax was okay, but the service failed to restart."
    fi
else
    sudo nginx -t
    fail "Nginx configuration test failed. Changes were not applied."
fi
