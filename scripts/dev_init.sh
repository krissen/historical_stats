#!/usr/bin/env bash
# scripts/dev_init.sh
# Run with 'source scripts/dev_init.sh'

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "❌ Run using 'source scripts/dev_init.sh' – not './scripts/dev_init.sh'"
  return 1
fi

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/" && pwd)"

if [ -f "$BASEDIR/.venv/bin/activate" ]; then
  source "$BASEDIR/.venv/bin/activate"
else
  echo "❌ Could not find .venv/. Run ./setup.sh first"
  return 1
fi

export PYTHONPATH="$BASEDIR/custom_components:$PYTHONPATH"
echo "✅ venv is active (for Home Assistant) and PYTHONPATH is set."

