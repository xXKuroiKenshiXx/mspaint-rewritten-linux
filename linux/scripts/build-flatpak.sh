#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
flatpak-builder --user --force-clean --repo=flatpak-repo flatpak-build packaging/flatpak.json
arch=$(uname -m)
flatpak build-bundle flatpak-repo "dist/packages/mspaint-rewritten-linux-0.1.0-$arch.flatpak" io.github.xXKuroiKenshiXx.MSPaint
