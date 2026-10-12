"""Recover the fork's own glyphs, retaining their exact pixels and color keys."""
import json
import re
from pathlib import Path
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt

root = Path(__file__).resolve().parents[1]
assets = root / "mspaint/assets"
assets.mkdir(parents=True, exist_ok=True)
objects = {}
for filename in ("PaintForm.dfm", "MenuForm.dfm", "SaveForm.dfm", "PropertiesForm.dfm"):
    source = (root.parent / filename).read_text(encoding="utf-8-sig")
    starts = list(re.finditer(r"^\s*object (\w+): (\w+)\s*$", source, re.M))
    for i, match in enumerate(starts):
        block = source[match.end():starts[i+1].start() if i+1 < len(starts) else len(source)]
        name, kind = match.groups()
        entry = {"type": kind, "file": filename}
        for key in ("Left", "Top", "Width", "Height", "Caption", "Align", "Tag", "Hint", "OnClick", "ImageName"):
            property = re.search(r"^\s*" + key + r" = ([^\r\n]+)", block, re.M)
            if property:
                entry[key] = property.group(1)
        data = re.search(r"(?:Glyph|BPicture|Picture)\.Data = \{([0-9A-Fa-f\s]+)\}", block)
        if data:
            raw = bytes.fromhex(data.group(1))
            offset = raw.find(b"BM")
            png_offset = raw.find(b"\x89PNG\r\n\x1a\n")
            if offset >= 0 or png_offset >= 0:
                image = QImage.fromData(raw[png_offset:] if png_offset>=0 else raw[offset:], "PNG" if png_offset>=0 else "BMP")
                if not image.isNull():
                    image = image.convertToFormat(QImage.Format.Format_ARGB32)
                    if png_offset<0:image.setAlphaChannel(image.createMaskFromColor(image.pixel(0, image.height()-1), Qt.MaskMode.MaskOutColor))
                    target = filename.removesuffix(".dfm") + "_" + name + ".png"
                    image.save(str(assets / target))
                    entry["glyph"] = target
                    entry["glyph_size"] = [image.width(), image.height()]
        objects[filename + ":" + name] = entry
    for i, match in enumerate(re.finditer(r"Image\.Data = \{([0-9A-Fa-f\s]+)\}", source)):
        raw = bytes.fromhex(match.group(1))
        offset = raw.find(b"\x89PNG\r\n\x1a\n")
        if offset >= 0:
            image = QImage.fromData(raw[offset:], "PNG")
            if not image.isNull():
                names = re.findall(r"Name = '([^']+)'", source[:match.start()])
                name = names[-1] if names else str(i)
                target = filename.removesuffix(".dfm") + "_collection_" + name + ".png"
                image.save(str(assets / target))
                objects[filename + ":collection:" + name] = {"glyph": target, "glyph_size": [image.width(), image.height()]}
(assets / "dfm-map.json").write_text(json.dumps(objects, indent=2) + "\n")
print("Extracted", len(list(assets.glob("*.png"))), "original glyphs")
