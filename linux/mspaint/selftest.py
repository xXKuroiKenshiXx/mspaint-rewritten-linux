"""Packaged-runtime checks, without a developer environment or pytest."""
import tempfile
import traceback
from pathlib import Path
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPainter, QTransform
from .document import Document, blank


def run():
    try:
        with tempfile.TemporaryDirectory(prefix="mspaint-selftest-") as folder:
            folder = Path(folder)
            doc = Document()
            doc.new(30, 20)
            doc.commit(blank(30, 20, "red"))
            for fmt in ("png", "bmp", "jpeg", "gif", "webp"):
                path = folder / ("drawing." + fmt)
                doc.save(path)
                other = Document()
                other.load(path)
                assert other.image.size() == doc.image.size(), fmt
                assert other.image.pixelColor(0, 0).red() > 240, fmt
            saved = doc.image.copy()
            doc.commit(blank(30, 20, "blue"))
            assert doc.dirty
            doc.undo()
            assert doc.image == saved and not doc.dirty
            doc.redo()
            assert doc.dirty
            doc.fill(QPoint(1, 1), "green")
            assert doc.image.pixelColor(1, 1) == QColor("green")
            doc.resize(40, 30)
            assert doc.image.pixelColor(39, 29) == QColor("white")
            doc.paste(blank(10, 10, "red"), QPoint(35, 25))
            assert doc.image.width() == 45 and doc.image.height() == 35
            invalid = folder / "corrupt.png"
            invalid.write_bytes(b"invalid image")
            before = doc.image.copy()
            try:
                doc.load(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid image accepted")
            assert doc.image == before
        print("Packaged self-test passed: PNG/BMP/JPEG/GIF/WebP, history, fill, resize, paste, corrupt input.")
        return 0
    except Exception:
        traceback.print_exc()
        return 1
