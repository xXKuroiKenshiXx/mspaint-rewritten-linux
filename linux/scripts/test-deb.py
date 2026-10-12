"""Install the generated .deb in a disposable Ubuntu container and test it."""
import subprocess
import sys
from pathlib import Path

folder = Path(sys.argv[1]).resolve()
if not (folder / "mspaint-rewritten-linux_0.1.0_amd64.deb").is_file():
    raise SystemExit("Missing amd64 Debian package")
command = ("apt-get update -qq && apt-get install --no-install-recommends -y "
           "/packages/mspaint-rewritten-linux_0.1.0_amd64.deb && "
           "QT_QPA_PLATFORM=offscreen mspaint-rewritten-linux --self-test && "
           "QT_QPA_PLATFORM=offscreen mspaint-rewritten-linux --smoke-test")
subprocess.run(["podman", "run", "--rm", "--network=host", "--security-opt=no-new-privileges",
                "-v", f"{folder}:/packages:ro", "docker.io/library/ubuntu:24.04", "sh", "-c", command],
               timeout=600, check=True)
