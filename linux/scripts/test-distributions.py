"""Headless packaged-executable startup checks in official OCI images.

Does not test real Wayland desktops, portals, printers or musl compatibility.
Dependencies are installed only inside disposable containers.
"""
import json
import subprocess
import sys
from pathlib import Path

bundle = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
output.mkdir(parents=True, exist_ok=True)
cases = {
    "ubuntu-24.04": ("docker.io/library/ubuntu:24.04", "apt-get update -qq && apt-get install --no-install-recommends -y libgl1 libegl1 libopengl0 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0t64"),
    "debian-13": ("docker.io/library/debian:13", "apt-get update -qq && apt-get install --no-install-recommends -y libgl1 libegl1 libopengl0 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0t64"),
    "fedora-44": ("registry.fedoraproject.org/fedora:44", "dnf install -y mesa-libEGL libglvnd-glx libglvnd-opengl libxkbcommon dbus-libs fontconfig glib2"),
    "arch": ("docker.io/library/archlinux:latest", "pacman -Syu --noconfirm libglvnd libxkbcommon dbus fontconfig glib2"),
    "void-glibc": ("ghcr.io/void-linux/void-glibc:latest", "xbps-install -Sy xbps && xbps-install -Sy libglvnd libxkbcommon dbus fontconfig glib"),
}
requested = sys.argv[3:]
if requested:
    cases = {key: cases[key] for key in requested}
results = []
for name, (image, setup) in cases.items():
    log_path = output / (name + ".log")
    command = setup + " && QT_QPA_PLATFORM=offscreen /opt/paint/mspaint-rewritten-linux --self-test && QT_QPA_PLATFORM=offscreen /opt/paint/mspaint-rewritten-linux --smoke-test"
    with log_path.open("w") as log:
        try:
            result = subprocess.run(["podman", "run", "--rm", "--network=host", "--security-opt=no-new-privileges",
                "-v", f"{bundle}:/opt/paint:ro", image, "sh", "-c", command],
                stdout=log, stderr=subprocess.STDOUT, timeout=600)
            status = "passed" if result.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            status = "timeout"
    inspect = subprocess.run(["podman", "image", "inspect", image, "--format", "{{.Digest}}"],
                             capture_output=True, text=True)
    results.append({"distribution": name, "image": image, "digest": inspect.stdout.strip(), "runtime_and_startup": status})
    (output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(name, status, flush=True)
raise SystemExit(0 if all(r["startup"] == "passed" for r in results) else 1)
