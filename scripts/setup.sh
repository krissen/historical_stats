#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

# Create venv if it does not exist
if [ ! -d ".venv" ]; then
  python3.13 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install requirements
python3 -m pip install --upgrade pip
python3 -m pip install --requirement requirements.txt
python3 -m pip install mutagen home-assistant-frontend

# Set PYTHONPATH for HA custom_components
export PYTHONPATH="$PWD/custom_components:$PYTHONPATH"

echo "✅  venv is ready and requirements installed. PYTHONPATH set."
echo "Now start HA with: hass --config \"$PWD/config\""

