#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install --break-system-packages pyinstaller

pyinstaller --noconfirm --onefile --windowed \
  --add-data "images:images" \
  --add-data "config.ini:." \
  --name "InventorySystem" \
  dashbord.py

echo "Build complete: dist/InventorySystem"
