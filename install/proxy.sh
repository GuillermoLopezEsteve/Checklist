#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }
[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"
[[ $EUID -eq 0 ]] || fail "This script must be run as sudo"

NGINX_LINK="/etc/nginx/sites-enabled/reverse-proxy"

SERVICE_NAME="checklist"
RUNTIME_DIR="/etc/${SERVICE_NAME}"
LOCAL_CONF="${RUNTIME_DIR}/config/proxy.conf"
SECRET_DIR="${RUNTIME_DIR}/.secret"

pending "Checking if Nginx is installed..."
command -v nginx >/dev/null 2>&1 && success "Nginx Installed" || fail "Nginx is not installed on this system."

pending "Checking if proxy conf exists in $LOCAL_CONF"
[[ -f "$LOCAL_CONF" ]] && success "Local conf exists" || fail "Local conf doesnt not exist $LOCAL_CONF"


pending "Checking if SSL certificates exist for proxy"

FOUND_SSL=true

[[ -f "${SECRET_DIR}/web.crt" ]] || { warn "SSL crt not found"; FOUND_SSL=false; }
[[ -f "${SECRET_DIR}/web.pem" ]] || { warn "SSL pem not found"; FOUND_SSL=false; }

if [[ "$FOUND_SSL" != true ]]; then
  read -rp "SSL certificates missing. Create self-signed certificate? [Y/n]: " ans
  if [[ ! "$ans" =~ ^[Nn]$ ]]; then
    pending "Creating self-signed SSL certificate"
    mkdir -p "$SECRET_DIR" || fail "Cannot create $SECRET_DIR"
    openssl req -x509 -nodes -newkey rsa:2048 \
      -keyout "${SECRET_DIR}/web.pem" \
      -out "${SECRET_DIR}/web.crt" \
      -days 365 \
      -subj "/CN=localhost" \
      && success "Self-signed SSL certificate created" \
      || fail "Failed to create SSL certificate"
  else
    warn "SSL certificates not created"
  fi
else
  success "SSL certificates found"
fi



FOUND_KEYS=true

[[ -f "${SECRET_DIR}/ACCESS_KEY_PROD" ]] || { warn "ACCESS_KEY_PROD not found"; FOUND_KEYS=false; }
[[ -f "${SECRET_DIR}/ACCESS_KEY_DEV"  ]] || { warn "ACCESS_KEY_DEV not found";  FOUND_KEYS=false; }

if [[ "$FOUND_KEYS" != true ]]; then
  read -rp "Access keys missing. Create SSH keys now? [Y/n]: " ans
  if [[ ! "$ans" =~ ^[Nn]$ ]]; then
    pending "Creating SSH keys in $SECRET_DIR"

    [[ -f "${SECRET_DIR}/ACCESS_KEY_PROD" ]] || \
      ssh-keygen -t ed25519 -N "" -f "${SECRET_DIR}/ACCESS_KEY_PROD" -C "checklist-prod" \
        && success "Created ACCESS_KEY_PROD" || fail "Failed to create ACCESS_KEY_PROD"

    [[ -f "${SECRET_DIR}/ACCESS_KEY_DEV" ]] || \
      ssh-keygen -t ed25519 -N "" -f "${SECRET_DIR}/ACCESS_KEY_DEV" -C "checklist-dev" \
        && success "Created ACCESS_KEY_DEV" || fail "Failed to create ACCESS_KEY_DEV"

    success "SSH keys ready"
  else
    warn "SSH keys not created"
    fail "Access keys must be placed in ${SECRET_DIR}"
  fi
else
  success "Access keys found"
fi



pending "Applying Nginx configuration..."

cp "$LOCAL_CONF" /etc/nginx/sites-available/reverse-proxy || fail "Failed to copy config to sites-available."
ln -sf /etc/nginx/sites-available/reverse-proxy "$NGINX_LINK" || fail "Failed to create symbolic link."

if [ -L /etc/nginx/sites-enabled/default ]; then
    pending "Disabling default Nginx site..."
    warn "Will delete nginx default sites"
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
