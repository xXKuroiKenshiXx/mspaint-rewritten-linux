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
    win.canvas.reset_transient()
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
    QTest.keyClick(window.canvas,Qt.Key.Key_Return)
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
    window.tool_combo.setCurrentText("Text")
    QTest.mouseClick(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
    QTest.keyClicks(window.canvas.text_editor,"Test text")
    window.tool_combo.setCurrentText("Pencil")
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
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
    QTest.mouseMove(window.canvas, QPoint(60, 60))
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(60, 60))
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


def test_free_selection_move_preserves_mask(window):
    from mspaint.document import blank
    from PySide6.QtGui import QPainterPath, QPolygon
    window.doc.commit(blank(100, 100, "red"))
    window.tool_combo.setCurrentText("Free select")
    path = QPainterPath()
    path.addPolygon(QPolygon([QPoint(10, 10), QPoint(30, 10), QPoint(10, 30)]))
    path.closeSubpath()
    window.canvas.selection_path = path
    window.canvas.selection = QRect(10, 10, 20, 20)
    before = window.doc.image.copy()
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(16, 16))
    QTest.mouseMove(window.canvas, QPoint(56, 56))
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=QPoint(56, 56))
    assert window.canvas.selection_path is not None
    assert window.canvas.selection.topLeft() == QPoint(50, 50)
    image = window.canvas.selected_image()
    assert image.pixelColor(18, 18).alpha() == 0
    assert image.pixelColor(2, 2).alpha() == 255
    window.canvas.transparent = True
    assert window.canvas.selected_image().pixelColor(18, 18).alpha() == 0
    window.doc.undo()
    assert window.doc.image == before


@pytest.mark.parametrize("tool",["Pencil","Fill","Text","Eraser","Color picker","Zoom","Rectangle","Ellipse","Line","Triangle","Star"])
def test_ribbon_buttons_select_the_actual_tool(window,tool):
    QTest.mouseClick(window.ribbon.tool_buttons[tool],Qt.MouseButton.LeftButton)
    assert window.canvas.tool==tool
    assert window.ribbon.tool_buttons[tool].isChecked()


def test_palette_can_change_secondary_without_changing_primary(window):
    original=QColor(window.canvas.foreground)
    QTest.mouseClick(window.ribbon.colors.second,Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.ribbon.colors.swatches[3],Qt.MouseButton.LeftButton)
    assert window.canvas.background==QColor("#ff0000")
    assert window.canvas.foreground==original


def test_inline_text_cancel_close_preserves_editability(window,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    QTest.mouseClick(window.ribbon.tool_buttons["Text"],Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(5,5))
    QTest.keyClicks(window.canvas.text_editor,"Editable")
    monkeypatch.setattr(QMessageBox,"question",lambda *args:QMessageBox.StandardButton.Cancel)
    assert not window.may_discard()
    assert window.canvas.text_editor.toPlainText()=="Editable"
    window.canvas.finish_text()
    assert window.doc.dirty


def test_selection_handles_resize_pixels_and_undo(window):
    from mspaint.document import blank
    window.doc.paste(blank(20,20,"red"),QPoint(10,10))
    before=window.doc.image.copy()
    window.tool_combo.setCurrentText("Select")
    window.canvas.selection=QRect(10,10,20,20)
    QTest.mousePress(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(29,29))
    QTest.mouseMove(window.canvas,QPoint(49,49))
    QTest.mouseRelease(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(49,49))
    assert window.doc.image.pixelColor(45,45)==QColor("red")
    window.doc.undo();assert window.doc.image==before


def test_shape_handles_keep_shape_editable_until_commit(window):
    QTest.mouseClick(window.ribbon.tool_buttons["Rectangle"],Qt.MouseButton.LeftButton)
    QTest.mousePress(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(10,10))
    QTest.mouseMove(window.canvas,QPoint(30,30))
    QTest.mouseRelease(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(30,30))
    assert window.canvas.shape_pending is not None
    assert not window.doc.dirty
    QTest.mousePress(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(30,30))
    QTest.mouseMove(window.canvas,QPoint(60,60))
    QTest.mouseRelease(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(60,60))
    assert window.canvas.selection.width()==51
    QTest.keyClick(window.canvas,Qt.Key.Key_Return);assert window.doc.dirty


def test_view_widgets_and_preview_lifetimes(window,app):
    window.ribbon.select_tab("View")
    window.ribbon.check_rulers.setChecked(False);assert window.workspace.horizontal.isHidden()
    window.ribbon.check_rulers.setChecked(True);assert not window.workspace.horizontal.isHidden()
    for _ in range(2):
        window.show_thumbnail(True);window.thumbnail_preview.close();app.processEvents()
        assert window.thumbnail_preview is None
        window.fullscreen();QTest.keyClick(window.fullscreen_preview,Qt.Key.Key_Escape);app.processEvents()
        assert window.fullscreen_preview is None


def test_text_handles_resize_without_rasterizing_and_snapshot_contains_text(window):
    QTest.mouseClick(window.ribbon.tool_buttons["Text"],Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(5,5))
    editor=window.canvas.text_editor
    QTest.keyClicks(editor,"Text")
    before=window.doc.image.copy()
    grip=editor.grips["br"]
    initial_width=editor.image_rect.width()
    QTest.mousePress(grip,Qt.MouseButton.LeftButton,pos=QPoint(2,2))
    QTest.mouseMove(grip,QPoint(25,25))
    QTest.mouseRelease(grip,Qt.MouseButton.LeftButton,pos=QPoint(25,25))
    assert editor.image_rect.width()>initial_width
    assert window.doc.image==before
    assert window.canvas.snapshot()!=before
    window.canvas.cancel_text()
    assert window.canvas.text_editor is None and window.doc.image==before


def test_curve_controls_remain_editable_and_commit_once(window):
    QTest.mouseClick(window.ribbon.tool_buttons["Curve"],Qt.MouseButton.LeftButton)
    canvas=window.canvas
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=QPoint(10,50))
    QTest.mouseMove(canvas,QPoint(90,50))
    QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=QPoint(90,50))
    QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=QPoint(30,10))
    QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=QPoint(70,90))
    assert canvas.shape_pending is not None and not window.doc.dirty
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=QPoint(30,10))
    QTest.mouseMove(canvas,QPoint(35,20))
    QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=QPoint(35,20))
    assert canvas.shape_pending["controls"][0]==QPoint(35,20)
    before=window.doc.image.copy()
    QTest.keyClick(canvas,Qt.Key.Key_Return)
    assert window.doc.dirty
    window.doc.undo();assert window.doc.image==before


def test_properties_units_roundtrip_and_invalid_dimensions(window):
    from mspaint.dialogs import PropertiesDialog
    dialog=PropertiesDialog(window)
    original=dialog.values()
    dialog.units[0].setChecked(True);dialog.units[1].setChecked(True);dialog.units[2].setChecked(True)
    assert dialog.values()==original
    dialog.width_edit.setText("999999");assert not dialog.ok.isEnabled()
    dialog.width_edit.setText("120");dialog.height_edit.setText("80")
    assert dialog.ok.isEnabled()
    dialog.apply();assert window.doc.image.size().width()==120
