"""Prepare relocatable AppDir, Debian package and portable tarball."""
import os
import platform
import shutil
import subprocess
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
bundle = root / "dist/mspaint-rewritten-linux"
out = root / "dist/packages"
out.mkdir(parents=True, exist_ok=True)
app_id = "io.github.xXKuroiKenshiXx.MSPaint"
version = "0.1.0"
machine = platform.machine()
architecture = {"x86_64": "amd64", "aarch64": "arm64"}.get(machine)
if architecture is None:
    raise SystemExit(f"Unsupported packaging architecture: {machine}")
if not (bundle / "mspaint-rewritten-linux").is_file():
    raise SystemExit("Run build.sh first")


def copy_bundle(destination):
    shutil.copytree(bundle, destination, dirs_exist_ok=True)


def metadata(destination):
    for source, target in [
        (f"{app_id}.desktop", "share/applications"),
        (f"{app_id}.svg", "share/icons/hicolor/scalable/apps"),
        (f"{app_id}.metainfo.xml", "share/metainfo"),
    ]:
        directory = destination / target
        directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / "packaging" / source, directory)


with tarfile.open(out / f"mspaint-rewritten-linux-{version}-linux-{machine}.tar.gz", "w:gz") as archive:
    archive.add(bundle, arcname="mspaint-rewritten-linux")

appdir = root / "build/AppDir"
if appdir.exists():
    if appdir.resolve().parent != (root / "build").resolve():
        raise SystemExit("Unsafe AppDir path")
    shutil.rmtree(appdir)
copy_bundle(appdir / "usr/lib/mspaint")
metadata(appdir / "usr")
shutil.copy2(root / "packaging" / f"{app_id}.desktop", appdir)
shutil.copy2(root / "packaging" / f"{app_id}.svg", appdir)
launcher = appdir / "AppRun"
launcher.write_text('#!/bin/sh\nbase=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec "$base/usr/lib/mspaint/mspaint-rewritten-linux" "$@"\n')
launcher.chmod(0o755)

deb = root / "build/debian"
if deb.exists():
    if deb.resolve().parent != (root / "build").resolve():
        raise SystemExit("Unsafe Debian staging path")
    shutil.rmtree(deb)
copy_bundle(deb / "opt/mspaint-rewritten-linux")
metadata(deb / "usr")
control = deb / "DEBIAN"
control.mkdir(parents=True, exist_ok=True)
(control / "control").write_text(f"""Package: mspaint-rewritten-linux
Version: {version}
Architecture: {architecture}
Maintainer: xXKuroiKenshiXx <noreply@github.com>
Section: graphics
Priority: optional
Depends: libc6 (>= 2.39), libgl1, libegl1, libopengl0, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-keysyms1, libxcb-shape0, libxcb-xinerama0, libxcb-randr0, libxcb-render-util0, libxcb-sync1, libxcb-xfixes0, libxcb1, libdbus-1-3, libfontconfig1, libfreetype6, libglib2.0-0t64
Description: Native Qt raster editor (preview)
 Linux adaptation of mspaint-rewritten. See repository for feature coverage.
""")
bin_dir = deb / "usr/bin"
bin_dir.mkdir(parents=True, exist_ok=True)
launcher = bin_dir / "mspaint-rewritten-linux"
launcher.write_text('#!/bin/sh\nexec /opt/mspaint-rewritten-linux/mspaint-rewritten-linux "$@"\n')
launcher.chmod(0o755)
subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(deb),
                str(out / f"mspaint-rewritten-linux_{version}_{architecture}.deb")], check=True)
