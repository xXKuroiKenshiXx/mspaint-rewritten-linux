import pytest
from PySide6.QtCore import QPoint, Qt, QRect
from PySide6.QtGui import QColor, QImage, QTransform
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtPrintSupport import QPrinter
from mspaint.app import Window


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path):
    from PySide6.QtCore import QSettings
    win = Window()
    win.settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    win.doc.new(100, 100)
    win.canvas.sync()
    win.show()
    app.processEvents()
    yield win
    win.doc.saved_key = win.doc.image.cacheKey()
    win.close()


@pytest.mark.parametrize("tool", ["Pencil", "Brush", "Eraser", "Airbrush", "Calligraphy", "Marker", "Watercolor", "Crayon",
    "Line", "Curve", "Rectangle", "Rounded rectangle", "Ellipse", "Triangle", "Diamond", "Star",
    "Pentagon", "Hexagon", "Arrow", "Right triangle", "Four-point star", "Six-point star",
    "Left arrow", "Up arrow", "Down arrow"])
def test_mouse_tools(window, tool):
    if tool == "Eraser":
        window.doc.image.fill(QColor("red"))
    original = window.doc.image.copy()
    window.tool_combo.setCurrentText(tool)
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
    QTest.mouseMove(window.canvas, QPoint(60, 60))
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(60, 60))
    if tool == "Curve":
        QTest.mouseClick(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(15, 50))
        QTest.mouseClick(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(50, 15))
    assert window.doc.image != original
    window.doc.undo()
    # Eraser test manually seeds image outside document history.
    if tool != "Eraser":
        assert window.doc.image == original


def test_selection_copy_paste_crop(window):
    window.canvas.selection = QRect(10, 10, 20, 15)
    window.copy()
    assert QApplication.clipboard().image().size() == window.canvas.selection.size()
    window.crop()
    assert window.doc.image.width() == 20
    window.history(False)
    assert window.doc.image.width() == 100
    QApplication.clipboard().setImage(QImage(120, 130, QImage.Format.Format_ARGB32))
    window.paste()
    assert window.doc.image.width() == 120
    assert window.doc.image.height() == 130


def test_rotate_flip_zoom_thumbnail_pdf(window, tmp_path):
    window.doc.new(20, 10)
    window.transform(QTransform().rotate(90))
    assert window.doc.image.width() == 10
    window.flip(True)
    window.set_zoom(4)
    assert window.canvas.width() == 40
    window.show_thumbnail(True)
    assert window.thumbnail.pixmap() is not None
    printer = QPrinter()
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    path = tmp_path / "drawing.pdf"
    printer.setOutputFileName(str(path))
    window.render_printer(printer)
    assert path.read_bytes().startswith(b"%PDF")


def test_free_selection_and_move(window):
    window.tool_combo.setCurrentText("Free select")
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
    for point in [QPoint(40, 10), QPoint(40, 40), QPoint(10, 40)]:
        QTest.mouseMove(window.canvas, point)
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
    assert window.canvas.selection_path is not None
    assert not window.canvas.selected_image().isNull()


def test_polygon(window):
    window.tool_combo.setCurrentText("Polygon")
    for point in [QPoint(10, 10), QPoint(60, 10), QPoint(30, 60)]:
        QTest.mouseClick(window.canvas, Qt.MouseButton.LeftButton, pos=point)
    QTest.keyClick(window.canvas, Qt.Key.Key_Return)
    assert window.doc.dirty


def test_text_and_cancelled_save_guard(window, monkeypatch):
    from PySide6.QtWidgets import QInputDialog, QMessageBox
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *args: ("Test text", True))
    window.tool_combo.setCurrentText("Text")
    QTest.mouseClick(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
    assert window.doc.dirty
    before = window.doc.image.copy()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    window.new()
    assert window.doc.image == before


def test_selection_move_is_single_undo_step(window):
    from mspaint.document import blank
    window.doc.commit(blank(100, 100, "blue"))
    window.doc.paste(blank(20, 20, "red"), QPoint(10, 10))
    before = window.doc.image.copy()
    window.tool_combo.setCurrentText("Select")
    window.canvas.selection = QRect(10, 10, 20, 20)
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(15, 15))
    QTest.mouseMove(window.canvas, QPoint(55, 55))
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(55, 55))
    assert window.doc.image.pixelColor(55, 55) == QColor("red")
    assert window.doc.image.pixelColor(15, 15) == QColor("white")
    window.doc.undo()
    assert window.doc.image == before


def test_transparent_selection(window):
    from mspaint.document import blank
    window.doc.commit(blank(100, 100))
    window.doc.paste(blank(10, 10, "red"), QPoint(10, 10))
    window.canvas.transparent = True
    window.canvas.selection = QRect(0, 0, 30, 30)
    image = window.canvas.selected_image()
    assert image.pixelColor(0, 0).alpha() == 0
    assert image.pixelColor(15, 15).alpha() == 255
