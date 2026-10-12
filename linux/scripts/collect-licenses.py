"""Collect notices and exact package source versions for distributed libraries."""
import json
import re
import shutil
import subprocess
import tarfile
import importlib.metadata
from pathlib import Path

root = Path(__file__).resolve().parents[1]
bundle = root / "dist/mspaint-rewritten-linux"
destination = bundle / "licenses"
destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(root.parent / "LICENSE", destination / "MSPaint-MIT.txt")
sources = {}
libraries = {}
for package in ("Pillow", "PyInstaller"):
    distribution = importlib.metadata.distribution(package)
    for file in distribution.files or []:
        if "/licenses/" in str(file) or "/sboms/" in str(file):
            source = distribution.locate_file(file)
            name = re.sub(r"[^A-Za-z0-9_.-]", "_", package + "_" + str(file))
            if source.is_file():
                shutil.copyfile(source, destination / name)
for library in sorted((bundle / "_internal").glob("*.so*")):
    query = subprocess.run(["dpkg-query", "-S", "*/" + library.name], capture_output=True, text=True)
    for line in query.stdout.splitlines():
        if ": " not in line:
            continue
        package = line.split(": ", 1)[0]
        if ", " in package:
            continue
        info = subprocess.run(["dpkg-query", "-W", "-f", "${source:Package}\t${source:Version}\t${Version}", package],
                              capture_output=True, text=True)
        if info.returncode != 0:
            continue
        values = info.stdout.split("\t")
        if len(values) != 3:
            continue
        source_package, source_version, binary_version = values
        source_package = source_package or package.split(":")[0]
        source_version = source_version or binary_version
        sources[source_package] = source_version
        libraries[library.name] = {"package": package, "version": binary_version,
                                   "source_package": source_package, "source_version": source_version}
        copyright = Path("/usr/share/doc") / package.split(":")[0] / "copyright"
        if copyright.exists():
            shutil.copyfile(copyright, destination / (package.replace(":", "-") + "-copyright.txt"))
        break

source_dir = root / "third-party-sources"
required = ["qtbase-6.12.0.tar.gz", "qtwayland-6.12.0.tar.gz", "qtsvg-6.12.0.tar.gz",
            "pyside-setup-6.12.0.tar.gz", "icu-73.2.tar.gz", "pillow-12.3.0.tar.gz"]
if not all((source_dir / name).is_file() for name in required):
    raise SystemExit("Run scripts/download-third-party.sh before packaging")
for archive in sorted(source_dir.glob("*.tar.gz")):
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if not member.isfile() or member.size > 1024 * 1024:
                continue
            parts = Path(member.name).parts[1:]
            if not parts:
                continue
            basename = parts[-1].lower()
            if "LICENSES" in parts or basename.startswith(("license", "copying", "copyright")) or basename == "qt_attribution.json":
                # Never extract untrusted paths; flatten names to an explicitly chosen folder.
                name = re.sub(r"[^A-Za-z0-9_.-]", "_", archive.stem + "_" + "_".join(parts))
                content = tar.extractfile(member)
                if content:
                    (destination / name).write_bytes(content.read())

(destination / "system-libraries.json").write_text(json.dumps(libraries, indent=2) + "\n")
(root / "build/source-packages.json").write_text(json.dumps(sources, indent=2) + "\n")
(destination / "README.txt").write_text("""MSPaint Rewritten Linux uses Qt/PySide6 6.12.0 under LGPL-3.0, and Python and other separately licensed libraries.
The application source is MIT-licensed. Copyright and license notices are in this folder.
The matching third-party source archive accompanies the release under third-party-sources.
All bundled shared libraries can be replaced. For AppImage, extract with --appimage-extract,
then replace libraries under squashfs-root/usr/lib/mspaint/_internal and run AppRun.
The portable tarball can likewise be unpacked and its _internal libraries replaced.
For Flatpak, rebuild from the repository with replacement shared libraries in dist.
No restrictions are imposed on debugging, reverse engineering, replacement or relinking.
Build scripts are in linux/scripts. Qt source build instructions are included in its sources.
""")
