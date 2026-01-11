
#!/usr/bin/env bash
# Convenience script — expects the project and a `.venv` in the same directory as this script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
  echo "Error: $PY not found or not executable." >&2
  echo "Create a venv in the same directory as this script with:" >&2
  echo "  cd \"$SCRIPT_DIR\" && python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements.txt" >&2
  exit 1
fi

cd "$SCRIPT_DIR" || exit 1

sudo "$PY" omen-fan.py service stop
sudo "$PY" omen-fan.py service start
