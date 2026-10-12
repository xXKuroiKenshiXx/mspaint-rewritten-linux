#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p third-party-sources
download() {
 local url="$1" filename="$2" hash="$3"
 if [ ! -f "third-party-sources/$filename" ]; then
  curl --fail --location --retry 3 "$url" -o "third-party-sources/$filename"
 fi
 printf '%s  %s\n' "$hash" "third-party-sources/$filename" | sha256sum --check
}
download https://codeload.github.com/qt/qtbase/tar.gz/refs/tags/v6.12.0 qtbase-6.12.0.tar.gz dff6570582c272cbe744d2e460700318262af505460f4215276459970ae31b46
download https://codeload.github.com/qt/qtwayland/tar.gz/refs/tags/v6.12.0 qtwayland-6.12.0.tar.gz 6a6ac145aaf34ab742f85ff79d688c5bab9160a1da32e7855c8e7278ff774f3c
download https://codeload.github.com/qt/qtsvg/tar.gz/refs/tags/v6.12.0 qtsvg-6.12.0.tar.gz 38d440c4e97c90ce4f5b76c65dcd63d716d2ef4852baa6fb0926fb94bb96ea66
download https://codeload.github.com/pyside/pyside-setup/tar.gz/refs/tags/v6.12.0 pyside-setup-6.12.0.tar.gz dce2a944b34320e51a0ec8100cb983956399b97dec386f0fbe39e1b52571a336
download https://codeload.github.com/unicode-org/icu/tar.gz/refs/tags/release-73-2 icu-73.2.tar.gz c15f704e83c221c0680640a995d9db641f5b82098fb4b258a94b7d0561493c88
download https://codeload.github.com/python-pillow/Pillow/tar.gz/refs/tags/12.3.0 pillow-12.3.0.tar.gz d7ce60fdf8b3d3b4370ea213834d7c852b1ca16396d4e75e5046be815b11b2fb
