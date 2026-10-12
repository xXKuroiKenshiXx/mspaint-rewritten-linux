"""Fetch redistributable, metric-compatible fonts from their official projects."""
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

target=Path(__file__).resolve().parents[1]/"mspaint/assets/fonts"
target.mkdir(parents=True,exist_ok=True)
def download(url,path):subprocess.run(["curl","--fail","--location","--retry","3",url,"-o",str(path)],check=True)
with tempfile.TemporaryDirectory(prefix="paint-fonts-") as folder:
    archive=Path(folder)/"selawik.zip"
    download("https://github.com/microsoft/Selawik/releases/download/1.01/Selawik_Release.zip",archive)
    with zipfile.ZipFile(archive) as source:
        for name in ("selawk.ttf","selawkb.ttf","selawkl.ttf","selawksb.ttf","selawksl.ttf"):
            (target/name).write_bytes(source.read(name))
download("https://raw.githubusercontent.com/microsoft/Selawik/master/LICENSE.txt",target/"Selawik-OFL.txt")
for name in ("Carlito-Regular.ttf","Carlito-Bold.ttf","Carlito-Italic.ttf","Carlito-BoldItalic.ttf","OFL.txt"):
    download("https://raw.githubusercontent.com/google/fonts/main/ofl/carlito/"+name,target/("Carlito-OFL.txt" if name=="OFL.txt" else name))
(target/"README.txt").write_text("Selawik 1.01 (Microsoft) is a Segoe UI metric-compatible font. Carlito (Google Fonts) is Calibri metric-compatible. Both are redistributed under the accompanying SIL Open Font Licenses. Original Windows fonts are not redistributed. Font software is unmodified.\n")
