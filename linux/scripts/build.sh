#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m PyInstaller --noconfirm --clean --onedir --name mspaint-rewritten-linux \
  --hidden-import PySide6.QtDBus \
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets \
  --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick \
  --add-data '../LICENSE:licenses' launcher.py
python scripts/collect-licenses.py
python scripts/package.py
