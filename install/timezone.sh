#!/usr/bin/env bash

GREEN="\033[0;32m";YELLOW="\033[0;33m";RED="\033[0;31m";CYAN="\033[0;36m";NC="\033[0m"
fail()    { echo -e "${RED}[ERROR  ] ${NC}$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] ${NC}$1"; }
warn()    { echo -e "${YELLOW}[WARN   ] ${NC}$1"; }
pending() { echo -e "${CYAN}[PENDING] ${NC}$1"; }

[[ -n "${BASH_VERSION:-}" ]] || fail "Must be runned as bash"
[[ $EUID -eq 0 ]] || fail "This script must be run as sudo"


read -rp "Change system timezone? [y/N]: " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  read -rp "Enter timezone (e.g. Europe/Madrid): " TZ
  timedatectl list-timezones | grep -qx "$TZ" || fail "Invalid timezone: $TZ"
  pending "Setting timezone to $TZ"
  timedatectl set-timezone "$TZ" && success "Timezone set to $TZ" || fail "Failed to set timezone"
else
  warn "Timezone unchanged"
fi
