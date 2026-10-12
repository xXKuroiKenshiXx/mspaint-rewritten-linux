import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPainter
from mspaint.document import Document, blank, valid_size


def test_corrupt_open_preserves_document_and_path(tmp_path):
    doc = Document()
    doc.commit(blank(4, 3, "red"))
    path = tmp_path / "drawing.png"
    doc.save(path)
    before = doc.image.copy()
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_bytes(b"not a picture")
    with pytest.raises(ValueError):
        doc.load(corrupt)
    assert doc.image == before
    assert doc.path == path
    assert not doc.dirty


@pytest.mark.parametrize("suffix", ["png", "bmp", "jpeg", "webp", "gif"])
def test_save_and_load(tmp_path, suffix):
    doc = Document()
    doc.commit(blank(10, 12, "red"))
    path = tmp_path / ("roundtrip." + suffix)
    doc.save(path)
    assert not doc.dirty
    other = Document()
    other.load(path)
    assert other.image.size() == doc.image.size()
    assert other.image.pixelColor(2, 2).red() > 240


def test_undo_redo_saved_state_and_branch(tmp_path):
    doc = Document()
    doc.commit(blank(3, 2, "red"))
    doc.save(tmp_path / "saved.png")
    doc.commit(blank(3, 2, "blue"))
    assert doc.dirty
    doc.undo()
    assert not doc.dirty
    doc.redo()
    assert doc.dirty
    doc.undo()
    doc.commit(blank(3, 2, "green"))
    doc.redo()
    assert doc.image.pixelColor(0, 0) == QColor("green")


def test_atomic_save_failure_preserves_old_file(tmp_path):
    doc = Document()
    path = tmp_path / "drawing.unknown"
    path.write_bytes(b"original")
    with pytest.raises(ValueError):
        doc.save(path)
    assert path.read_bytes() == b"original"
    assert doc.path is None


def test_resize_and_paste_are_single_undo_steps():
    doc = Document()
    doc.new(3, 2)
    doc.resize(5, 4, background="blue")
    assert doc.image.pixelColor(4, 3) == QColor("blue")
    doc.undo()
    assert doc.image.width() == 3
    doc.paste(blank(4, 4, "red"), QPoint(2, 1))
    assert doc.image.width() == 6
    assert doc.image.height() == 5
    assert doc.image.pixelColor(3, 2) == QColor("red")
    doc.undo()
    assert doc.image.width() == 3


def test_fill_respects_boundary_and_handles_same_color():
    doc = Document()
    doc.new(7, 7)
    image = doc.image.copy()
    painter = QPainter(image)
    painter.setPen(QColor("black"))
    painter.drawRect(1, 1, 4, 4)
    painter.end()
    doc.commit(image)
    doc.fill(QPoint(3, 3), "red")
    assert doc.image.pixelColor(3, 3) == QColor("red")
    assert doc.image.pixelColor(0, 0) == QColor("white")
    before = len(doc.history)
    doc.fill(QPoint(3, 3), "red")
    assert len(doc.history) == before
    doc.undo()
    assert doc.image.pixelColor(3, 3) == QColor("white")


@pytest.mark.parametrize("width,height", [(0, 1), (-1, 1), (1, 32768), (32767, 32767)])
def test_canvas_limits(width, height):
    with pytest.raises(ValueError):
        valid_size(width, height)


def test_history_is_bounded():
    doc = Document()
    doc.new(2, 2)
    for i in range(70):
        doc.commit(blank(2, 2, QColor(i, 0, 0)))
    assert len(doc.history) <= 50


def test_new_clears_filename_and_history(tmp_path):
    doc = Document()
    doc.save(tmp_path / "old.png")
    doc.commit(blank(2, 2, "red"))
    doc.new()
    assert doc.path is None
    assert not doc.dirty
    assert len(doc.history) == 1
