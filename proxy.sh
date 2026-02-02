#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }
[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"

LOCAL_CONF="/etc/checklist/config/proxy.conf"
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

cp "$LOCAL_CONF" /etc/nginx/sites-available/reverse-proxy || fail "Failed to copy config to sites-available."
ln -sf /etc/nginx/sites-available/reverse-proxy "$NGINX_LINK" || fail "Failed to create symbolic link."

if [ -L /etc/nginx/sites-enabled/default ]; then
    pending "Disabling default Nginx site..."
    rm /etc/nginx/sites-enabled/default && success "Default site disabled." || fail "Could not remove default link."
fi

pending "Testing Nginx configuration syntax..."
if nginx -t >/dev/null 2>&1; then
    success "Nginx configuration syntax is valid."
    pending "Restarting Nginx..."
    if systemctl restart nginx; then
        success "Nginx restarted successfully."
    else
        fail "Nginx syntax was okay, but the service failed to restart."
    fi
else
    sudo nginx -t
    fail "Nginx configuration test failed. Changes were not applied."
fi
