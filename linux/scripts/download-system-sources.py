"""Download corresponding Ubuntu source archives into the release source mirror.

Uses a private apt source configuration and package lists, never edits host apt sources.
Run collect-licenses.py before this script on the Ubuntu build host.
"""
import json
import subprocess
import hashlib
import re
from urllib.parse import urlencode, urlparse, unquote
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = root / "build/source-apt.list"
lists = root / "build/source-apt-lists"
(lists / "partial").mkdir(parents=True, exist_ok=True)
config.write_text("""deb-src http://archive.ubuntu.com/ubuntu noble main universe
deb-src http://archive.ubuntu.com/ubuntu noble-updates main universe
deb-src http://security.ubuntu.com/ubuntu noble-security main universe
""")
options = ["-o", f"Dir::Etc::sourcelist={config}", "-o", "Dir::Etc::sourceparts=-",
           "-o", f"Dir::State::lists={lists}"]
subprocess.run(["apt-get", *options, "update"], check=True)
destination = root / "third-party-sources/ubuntu"
destination.mkdir(parents=True, exist_ok=True)
packages = json.loads((root / "build/source-packages.json").read_text())
unavailable_permissive = []

def archived_source(name, version):
    # Superseded source publications remain on Ubuntu's official Launchpad archive.
    query = urlencode({"ws.op": "getPublishedSources", "source_name": name,
                       "version": version, "exact_match": "true"})
    def request(url):
        return subprocess.check_output(["curl", "-4", "--fail", "--silent", "--show-error", "--location",
                                        "--connect-timeout", "20", "--max-time", "120", url])
    publications = json.loads(request("https://api.launchpad.net/1.0/ubuntu/+archive/primary?" + query))["entries"]
    if not publications:
        raise RuntimeError(f"No corresponding source found for {name} {version}")
    publication = publications[0]["self_link"]
    if not publication.startswith("https://api.launchpad.net/"):
        raise RuntimeError("Unexpected archive URL")
    urls = json.loads(request(publication + "?ws.op=sourceFileUrls"))
    downloaded = []
    for url in urls:
        if urlparse(url).hostname not in ("launchpad.net", "launchpadlibrarian.net"):
            raise RuntimeError("Unexpected source download host")
        filename = unquote(urlparse(url).path.split("/")[-1])
        if filename != Path(filename).name or not filename:
            raise RuntimeError("Invalid archive filename")
        target = destination / filename
        if not target.exists():
            temporary = target.with_name(target.name + ".partial")
            subprocess.run(["curl", "-4", "--fail", "--location", "--retry", "3", "--connect-timeout", "20",
                            "--max-time", "300", url, "-o", str(temporary)], check=True)
            temporary.rename(target)
        downloaded.append(target)
    dsc = next((p for p in downloaded if p.suffix == ".dsc"), None)
    if dsc is None:
        raise RuntimeError("Missing source control file")
    checksums = re.search(r"Checksums-Sha256:\n((?: [^\n]+\n)+)", dsc.read_text())
    if checksums is None:
        raise RuntimeError("Missing source checksums")
    for line in checksums.group(1).splitlines():
        digest, size, filename = line.split()
        if filename != Path(filename).name:
            raise RuntimeError("Invalid source filename")
        target = destination / filename
        if not target.exists() or target.stat().st_size != int(size) or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Source checksum mismatch: {filename}")
    print("Retrieved archived source:", name, version, flush=True)

for name, version in packages.items():
    result = subprocess.run(["apt-get", *options, "source", "--download-only", f"{name}={version}"], cwd=destination)
    if result.returncode != 0:
        if name == "krb5":
            # The distributed Kerberos shared libraries are under the permissive
            # MIT Kerberos/BSD terms reproduced in licenses/*krb5*copyright.txt.
            # A source mirror is optional for these libraries; never silently
            # treat an unavailable GPL/LGPL source as optional.
            unavailable_permissive.append({"package": name, "version": version,
                "reason": "Superseded source unavailable; permissive MIT Kerberos/BSD notices included"})
        else:
            archived_source(name, version)
    (root / "third-party-sources/unavailable-permissive-sources.json").write_text(json.dumps(unavailable_permissive, indent=2) + "\n")
