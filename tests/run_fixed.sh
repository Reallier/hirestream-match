#!/usr/bin/env bash
set -euo pipefail

PROFILE=${1:-prod_readonly}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_FILE="$SCRIPT_DIR/.env.${PROFILE}.local"
VENV_PY="$SCRIPT_DIR/../.venv/bin/python"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ -x "$VENV_PY" ]]; then
  "$VENV_PY" "$SCRIPT_DIR/run_tests.py" --profile "$PROFILE"
else
  python3 "$SCRIPT_DIR/run_tests.py" --profile "$PROFILE"
fi
