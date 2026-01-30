#!/bin/sh

if [ -z "${BASH_VERSION:-}" ]; then
  if command -v bash >/dev/null 2>&1; then
    exec bash "$0" "$@"
  else
    printf '\033[31mERROR:\033[0m bash is required but not found.\n' >&2
    exit 1
  fi
fi

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="$BASE_DIR/../logs"

PYTHON=/usr/bin/python3
SCRIPT1="$BASE_DIR/class/excel.py"
SCRIPT2="$BASE_DIR/class/launcher.py"
JOB2_ARGS=("$@")

mkdir -p "$LOGDIR"

printf '\033[33mDELETING ALL existing cron jobs for this user\033[0m\n'
crontab -r 2>/dev/null || true

escape_args() {
  printf '%q ' "$@"
}

SERVER_ARGS_ESCAPED="$(escape_args "${JOB2_ARGS[@]}")"

printf '\033[33mCREATING cron jobs for this user\033[0m\n'
(
  crontab -l 2>/dev/null
  echo "*/3 * * * * $PYTHON $SCRIPT1 >> $LOGDIR/cron_excel.log 2>&1"
  echo "*/3 * * * * $PYTHON $SCRIPT2 $SERVER_ARGS_ESCAPED >> $LOGDIR/cron_launcher.log 2>&1"
) | crontab -


echo "Cron jobs installed:"
crontab -l
