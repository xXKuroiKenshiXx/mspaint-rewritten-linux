#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/tools
arch=$(uname -m)
case "$arch" in
 x86_64) hash=95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6 ;;
 aarch64) hash=a595ea34cd6136c7f595e9dcbb16f3e9725d7610efb9e43b38c3c6e86cafc270 ;;
 *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
esac
tool="build/tools/appimagetool-$arch.AppImage"
curl --fail --location "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$arch.AppImage" -o "$tool"
printf '%s  %s\n' "$hash" "$tool" | sha256sum --check
chmod +x "$tool"
ARCH="$arch" "$tool" --appimage-extract-and-run build/AppDir "dist/packages/mspaint-rewritten-linux-0.1.0-$arch.AppImage"
